"""Pydantic schemas for request/response validation."""
from mybudget.schemas.account import (
    AccountCreate,
    AccountListResponse,
    AccountResponse,
    AccountUpdate,
)
from mybudget.schemas.categorization_rule import (
    CategorizationRuleCreate,
    CategorizationRuleListResponse,
    CategorizationRuleMatch,
    CategorizationRuleResponse,
    CategorizationRuleUpdate,
    CategorizationRuleWithCategoryResponse,
)
from mybudget.schemas.category import (
    CategoryCreate,
    CategoryGroupCreate,
    CategoryGroupResponse,
    CategoryGroupUpdate,
    CategoryGroupWithCategoriesResponse,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithGroupResponse,
)
from mybudget.schemas.reconciliation import (
    ReconciliationAdjustmentResponse,
    ReconciliationBalanceResponse,
    ReconciliationCreate,
    ReconciliationCreateAdjustment,
    ReconciliationListResponse,
    ReconciliationMarkCleared,
    ReconciliationResponse,
    ReconciliationUnmarkCleared,
    TransactionClearedResponse,
)
from mybudget.schemas.target import (
    CategoryTargetCreate,
    CategoryTargetResponse,
    CategoryTargetUpdate,
    UnderfundedResponse,
)
from mybudget.schemas.transaction import (
    TransactionApprove,
    TransactionBulkApprove,
    TransactionBulkResult,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
    TransactionWithDetailsResponse,
)
from mybudget.schemas.user import UserCreate, UserLogin, UserResponse

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
