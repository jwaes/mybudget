#!/bin/bash
# Database restore script for MyBudget
# Usage: ./restore.sh <backup_file>
#
# Features:
# - Reads DATABASE_URL from environment or .env file
# - Confirms before restoring (destructive operation)
# - Supports .sql and .sql.gz files
# - Creates a backup before restoring (safety)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backups"
BACKEND_DIR="$(dirname "${SCRIPT_DIR}")"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Show usage
usage() {
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Restore a PostgreSQL database from a backup file."
    echo ""
    echo "Arguments:"
    echo "  backup_file    Path to the backup file (.sql or .sql.gz)"
    echo ""
    echo "Options:"
    echo "  -y, --yes      Skip confirmation prompt"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 backups/mybudget_20240115_120000.sql.gz"
    echo "  $0 -y /path/to/backup.sql"
    exit 1
}

# Load DATABASE_URL from environment or .env file
load_database_url() {
    if [[ -n "${DATABASE_URL:-}" ]]; then
        log_info "Using DATABASE_URL from environment"
        return 0
    fi

    # Try .env file in backend directory
    local env_file="${BACKEND_DIR}/.env"
    if [[ -f "${env_file}" ]]; then
        log_info "Loading DATABASE_URL from ${env_file}"
        # shellcheck disable=SC1090
        set -a
        source "${env_file}"
        set +a
        if [[ -n "${DATABASE_URL:-}" ]]; then
            return 0
        fi
    fi

    # Try .env file in project root
    env_file="$(dirname "${BACKEND_DIR}")/.env"
    if [[ -f "${env_file}" ]]; then
        log_info "Loading DATABASE_URL from ${env_file}"
        # shellcheck disable=SC1090
        set -a
        source "${env_file}"
        set +a
        if [[ -n "${DATABASE_URL:-}" ]]; then
            return 0
        fi
    fi

    log_error "DATABASE_URL not found in environment or .env files"
    exit 1
}

# Parse DATABASE_URL into components
# Format: postgres://user:password@host:port/dbname
parse_database_url() {
    local url="${DATABASE_URL}"

    # Remove protocol prefix
    url="${url#postgres://}"
    url="${url#postgresql://}"

    # Extract user:password
    local userpass="${url%%@*}"
    url="${url#*@}"

    DB_USER="${userpass%%:*}"
    DB_PASS="${userpass#*:}"

    # Extract host:port
    local hostport="${url%%/*}"
    DB_NAME="${url#*/}"

    # Remove query parameters from dbname
    DB_NAME="${DB_NAME%%\?*}"

    # Parse host and port
    if [[ "${hostport}" == *:* ]]; then
        DB_HOST="${hostport%%:*}"
        DB_PORT="${hostport#*:}"
    else
        DB_HOST="${hostport}"
        DB_PORT="5432"
    fi

    # Validate parsed values
    if [[ -z "${DB_USER}" || -z "${DB_HOST}" || -z "${DB_NAME}" ]]; then
        log_error "Failed to parse DATABASE_URL"
        log_error "Expected format: postgres://user:password@host:port/dbname"
        exit 1
    fi

    log_info "Database: ${DB_NAME} on ${DB_HOST}:${DB_PORT}"
}

# Create safety backup before restore
create_safety_backup() {
    local safety_backup="${BACKUP_DIR}/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"

    mkdir -p "${BACKUP_DIR}"

    log_info "Creating safety backup before restore: ${safety_backup}"

    export PGPASSWORD="${DB_PASS}"

    if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        --no-owner --no-acl --clean --if-exists \
        2>/dev/null | gzip > "${safety_backup}"; then

        if [[ -s "${safety_backup}" ]]; then
            local size
            size=$(du -h "${safety_backup}" | cut -f1)
            log_info "Safety backup created: ${safety_backup} (${size})"
        else
            log_warn "Safety backup is empty (database may be new)"
            rm -f "${safety_backup}"
        fi
    else
        log_warn "Could not create safety backup (database may not exist yet)"
        rm -f "${safety_backup}"
    fi

    unset PGPASSWORD
}

# Restore from backup
restore_backup() {
    local backup_file="$1"

    log_info "Restoring from: ${backup_file}"

    export PGPASSWORD="${DB_PASS}"

    # Determine if file is compressed
    if [[ "${backup_file}" == *.gz ]]; then
        log_info "Decompressing and restoring..."
        if gunzip -c "${backup_file}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
            --quiet --single-transaction 2>&1; then
            log_info "Restore completed successfully"
        else
            unset PGPASSWORD
            log_error "Restore failed"
            exit 1
        fi
    else
        log_info "Restoring from uncompressed backup..."
        if psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
            --quiet --single-transaction -f "${backup_file}" 2>&1; then
            log_info "Restore completed successfully"
        else
            unset PGPASSWORD
            log_error "Restore failed"
            exit 1
        fi
    fi

    unset PGPASSWORD
}

# Main
main() {
    local skip_confirm=false
    local backup_file=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -y|--yes)
                skip_confirm=true
                shift
                ;;
            -h|--help)
                usage
                ;;
            -*)
                log_error "Unknown option: $1"
                usage
                ;;
            *)
                if [[ -z "${backup_file}" ]]; then
                    backup_file="$1"
                else
                    log_error "Too many arguments"
                    usage
                fi
                shift
                ;;
        esac
    done

    # Validate backup file argument
    if [[ -z "${backup_file}" ]]; then
        log_error "No backup file specified"
        usage
    fi

    # Resolve relative path to absolute
    if [[ "${backup_file}" != /* ]]; then
        # Check if it's relative to backups directory
        if [[ -f "${BACKUP_DIR}/${backup_file}" ]]; then
            backup_file="${BACKUP_DIR}/${backup_file}"
        elif [[ -f "${SCRIPT_DIR}/${backup_file}" ]]; then
            backup_file="${SCRIPT_DIR}/${backup_file}"
        elif [[ -f "$(pwd)/${backup_file}" ]]; then
            backup_file="$(pwd)/${backup_file}"
        fi
    fi

    # Check if backup file exists
    if [[ ! -f "${backup_file}" ]]; then
        log_error "Backup file not found: ${backup_file}"
        echo ""
        echo "Available backups:"
        if [[ -d "${BACKUP_DIR}" ]]; then
            ls -la "${BACKUP_DIR}"/*.sql* 2>/dev/null || echo "  No backups found in ${BACKUP_DIR}"
        else
            echo "  Backup directory does not exist: ${BACKUP_DIR}"
        fi
        exit 1
    fi

    # Validate file extension
    if [[ "${backup_file}" != *.sql && "${backup_file}" != *.sql.gz ]]; then
        log_error "Invalid backup file format. Expected .sql or .sql.gz"
        exit 1
    fi

    log_info "Starting database restore..."

    load_database_url
    parse_database_url

    # Confirmation prompt
    if [[ "${skip_confirm}" != true ]]; then
        echo ""
        echo -e "${YELLOW}WARNING: This will restore the database from:${NC}"
        echo "  ${backup_file}"
        echo ""
        echo -e "${YELLOW}Target database:${NC}"
        echo "  Host:     ${DB_HOST}:${DB_PORT}"
        echo "  Database: ${DB_NAME}"
        echo "  User:     ${DB_USER}"
        echo ""
        echo -e "${RED}This operation will OVERWRITE existing data!${NC}"
        echo ""
        read -rp "Are you sure you want to continue? [y/N] " confirm

        if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
            log_info "Restore cancelled by user"
            exit 0
        fi
    fi

    # Create safety backup
    create_safety_backup

    # Perform restore
    restore_backup "${backup_file}"

    log_info "Database restore completed successfully"
}

main "$@"
