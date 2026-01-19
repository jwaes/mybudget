#!/bin/bash
# Database backup script for MyBudget
# Usage: ./backup.sh [backup_name]
#
# Features:
# - Reads DATABASE_URL from environment or .env file
# - Creates timestamped backup if no name provided
# - Compresses with gzip
# - Stores in backups/ directory
# - Keeps last 7 daily backups (cleanup old ones)

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

# Number of backups to keep
KEEP_BACKUPS=7

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
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

# Create backup
create_backup() {
    local backup_name="${1:-}"

    # Generate backup filename
    if [[ -z "${backup_name}" ]]; then
        backup_name="${DB_NAME}_$(date +%Y%m%d_%H%M%S)"
    fi

    local backup_file="${BACKUP_DIR}/${backup_name}.sql.gz"

    # Ensure backup directory exists
    mkdir -p "${BACKUP_DIR}"

    log_info "Creating backup: ${backup_file}"

    # Set password for pg_dump
    export PGPASSWORD="${DB_PASS}"

    # Create backup with pg_dump and compress
    if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        --no-owner --no-acl --clean --if-exists \
        | gzip > "${backup_file}"; then

        unset PGPASSWORD

        # Verify backup was created and has content
        if [[ -s "${backup_file}" ]]; then
            local size
            size=$(du -h "${backup_file}" | cut -f1)
            log_info "Backup created successfully: ${backup_file} (${size})"
            echo "${backup_file}"
        else
            log_error "Backup file is empty"
            rm -f "${backup_file}"
            exit 1
        fi
    else
        unset PGPASSWORD
        log_error "pg_dump failed"
        rm -f "${backup_file}"
        exit 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (keeping last ${KEEP_BACKUPS})"

    # Find and sort backup files by modification time
    local count=0
    while IFS= read -r -d '' file; do
        ((count++))
        if [[ ${count} -gt ${KEEP_BACKUPS} ]]; then
            log_info "Removing old backup: $(basename "${file}")"
            rm -f "${file}"
        fi
    done < <(find "${BACKUP_DIR}" -name "*.sql.gz" -type f -printf '%T@\t%p\0' \
        | sort -zrn \
        | cut -z -f2-)

    if [[ ${count} -le ${KEEP_BACKUPS} ]]; then
        log_info "No old backups to remove (${count} backups exist)"
    fi
}

# Main
main() {
    local backup_name="${1:-}"

    log_info "Starting database backup..."

    load_database_url
    parse_database_url
    create_backup "${backup_name}"
    cleanup_old_backups

    log_info "Backup completed successfully"
}

main "$@"
