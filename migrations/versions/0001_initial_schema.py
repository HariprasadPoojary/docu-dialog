"""Create the initial users, projects, and documents schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name="fk_projects_owner_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="queued", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("size_bytes >= 0", name="ck_documents_size_nonnegative"),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'ready', 'failed')", name="ck_documents_valid_status"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_documents_project_id_projects", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
        sa.UniqueConstraint("storage_key", name="uq_documents_storage_key"),
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"], unique=False)
    op.create_index("ix_documents_project_status", "documents", ["project_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_documents_project_status", table_name="documents")
    op.drop_index("ix_documents_project_id", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_projects_owner_id", table_name="projects")
    op.drop_table("projects")
    op.drop_table("users")
