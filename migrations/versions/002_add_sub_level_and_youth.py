"""Add sub_level, organization_type columns and migrate club to youth.

Revision ID: 002
Revises:
Create Date: 2026-02-09
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add sub_level to schools
    op.add_column("schools", sa.Column("sub_level", sa.String(50), nullable=True))
    op.create_index("ix_schools_sub_level", "schools", ["sub_level"])

    # Add organization_type to schools
    op.add_column("schools", sa.Column("organization_type", sa.String(100), nullable=True))

    # Add sub_level to coaches
    op.add_column("coaches", sa.Column("sub_level", sa.String(50), nullable=True))
    op.create_index("ix_coaches_sub_level", "coaches", ["sub_level"])

    # Migrate club -> youth
    op.execute("UPDATE schools SET level = 'youth' WHERE level = 'club'")
    op.execute("UPDATE coaches SET level = 'youth' WHERE level = 'club'")


def downgrade():
    # Migrate youth -> club
    op.execute("UPDATE schools SET level = 'club' WHERE level = 'youth'")
    op.execute("UPDATE coaches SET level = 'club' WHERE level = 'youth'")

    # Drop sub_level from coaches
    op.drop_index("ix_coaches_sub_level", "coaches")
    op.drop_column("coaches", "sub_level")

    # Drop organization_type from schools
    op.drop_column("schools", "organization_type")

    # Drop sub_level from schools
    op.drop_index("ix_schools_sub_level", "schools")
    op.drop_column("schools", "sub_level")
