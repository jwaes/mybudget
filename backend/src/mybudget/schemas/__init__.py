"""Pydantic schemas for request/response validation."""
from mybudget.schemas.user import UserCreate, UserResponse, UserLogin
from mybudget.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountListResponse,
)
from mybudget.schemas.category import (
    CategoryGroupCreate,
    CategoryGroupUpdate,
    CategoryGroupResponse,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithGroupResponse,
    CategoryGroupWithCategoriesResponse,
    CategoryListResponse,
)
from mybudget.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionApprove,
    TransactionResponse,
    TransactionWithDetailsResponse,
    TransactionListResponse,
    TransactionBulkApprove,
    TransactionBulkResult,
)
from mybudget.schemas.categorization_rule import (
    CategorizationRuleCreate,
    CategorizationRuleUpdate,
    CategorizationRuleResponse,
    CategorizationRuleWithCategoryResponse,
    CategorizationRuleListResponse,
    CategorizationRuleMatch,
)
from mybudget.schemas.target import (
    CategoryTargetCreate,
    CategoryTargetUpdate,
    CategoryTargetResponse,
    UnderfundedResponse,
)
from mybudget.schemas.reconciliation import (
    ReconciliationCreate,
    ReconciliationMarkCleared,
    ReconciliationUnmarkCleared,
    ReconciliationCreateAdjustment,
    ReconciliationResponse,
    ReconciliationBalanceResponse,
    ReconciliationAdjustmentResponse,
    ReconciliationListResponse,
    TransactionClearedResponse,
)

__all__ = [
    # User
    "UserCreate",
    "UserResponse",
    "UserLogin",
    # Account
    "AccountCreate",
    "AccountUpdate",
    "AccountResponse",
    "AccountListResponse",
    # Category
    "CategoryGroupCreate",
    "CategoryGroupUpdate",
    "CategoryGroupResponse",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CategoryWithGroupResponse",
    "CategoryGroupWithCategoriesResponse",
    "CategoryListResponse",
    # Transaction
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionApprove",
    "TransactionResponse",
    "TransactionWithDetailsResponse",
    "TransactionListResponse",
    "TransactionBulkApprove",
    "TransactionBulkResult",
    # Categorization Rule
    "CategorizationRuleCreate",
    "CategorizationRuleUpdate",
    "CategorizationRuleResponse",
    "CategorizationRuleWithCategoryResponse",
    "CategorizationRuleListResponse",
    "CategorizationRuleMatch",
    # Target
    "CategoryTargetCreate",
    "CategoryTargetUpdate",
    "CategoryTargetResponse",
    "UnderfundedResponse",
    # Reconciliation
    "ReconciliationCreate",
    "ReconciliationMarkCleared",
    "ReconciliationUnmarkCleared",
    "ReconciliationCreateAdjustment",
    "ReconciliationResponse",
    "ReconciliationBalanceResponse",
    "ReconciliationAdjustmentResponse",
    "ReconciliationListResponse",
    "TransactionClearedResponse",
]
