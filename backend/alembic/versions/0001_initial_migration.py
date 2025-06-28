"""Initial migration

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('portfolio_url', sa.String(length=500), nullable=True),
        sa.Column('target_titles', sa.JSON(), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('years_experience', sa.Integer(), nullable=True),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('location_preferences', sa.JSON(), nullable=True),
        sa.Column('remote_preference', sa.Boolean(), nullable=True),
        sa.Column('resume_template_path', sa.String(length=500), nullable=True),
        sa.Column('cover_letter_template', sa.Text(), nullable=True),
        sa.Column('linkedin_username', sa.String(length=255), nullable=True),
        sa.Column('linkedin_password', sa.String(length=255), nullable=True),
        sa.Column('indeed_username', sa.String(length=255), nullable=True),
        sa.Column('indeed_password', sa.String(length=255), nullable=True),
        sa.Column('auto_apply_enabled', sa.Boolean(), nullable=True),
        sa.Column('notification_preferences', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('application_url', sa.String(length=500), nullable=False),
        sa.Column('platform', sa.Enum('linkedin', 'indeed', 'builtin', 'ziprecruiter', name='jobplatform'), nullable=False),
        sa.Column('platform_id', sa.String(length=100), nullable=True),
        sa.Column('fit_score', sa.Float(), nullable=True),
        sa.Column('priority', sa.Enum('must_apply', 'good_fit', 'stretch', 'low_priority', name='jobpriority'), nullable=True),
        sa.Column('status', sa.Enum('discovered', 'filtered', 'applied', 'under_review', 'interview_scheduled', 'rejected', 'offer_received', 'withdrawn', name='jobstatus'), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('response_deadline', sa.DateTime(), nullable=True),
        sa.Column('posted_date', sa.DateTime(), nullable=True),
        sa.Column('discovered_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_remote', sa.Boolean(), nullable=True),
        sa.Column('is_hybrid', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_company'), 'jobs', ['company'], unique=False)
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_platform_id'), 'jobs', ['platform_id'], unique=True)
    op.create_index(op.f('ix_jobs_title'), 'jobs', ['title'], unique=False)

    # Create applications table
    op.create_table('applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'submitted', 'failed', 'withdrawn', name='applicationstatus'), nullable=True),
        sa.Column('method', sa.Enum('automated', 'manual', 'semi_automated', name='applicationmethod'), nullable=True),
        sa.Column('submission_id', sa.String(length=255), nullable=True),
        sa.Column('resume_path', sa.String(length=500), nullable=True),
        sa.Column('cover_letter_path', sa.String(length=500), nullable=True),
        sa.Column('portfolio_url', sa.String(length=500), nullable=True),
        sa.Column('salary_expectation', sa.String(length=100), nullable=True),
        sa.Column('availability_date', sa.String(length=100), nullable=True),
        sa.Column('work_authorization', sa.String(length=100), nullable=True),
        sa.Column('custom_responses', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_applications_id'), 'applications', ['id'], unique=False)

    # Create communications table
    op.create_table('communications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('email', 'phone', 'message', 'interview', name='communicationtype'), nullable=False),
        sa.Column('direction', sa.Enum('inbound', 'outbound', name='communicationdirection'), nullable=False),
        sa.Column('status', sa.Enum('sent', 'received', 'scheduled', 'failed', name='communicationstatus'), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('sender_email', sa.String(length=255), nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_automated', sa.Boolean(), nullable=True),
        sa.Column('template_used', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communications_id'), 'communications', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_communications_id'), table_name='communications')
    op.drop_table('communications')
    op.drop_index(op.f('ix_applications_id'), table_name='applications')
    op.drop_table('applications')
    op.drop_index(op.f('ix_jobs_title'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_platform_id'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_company'), table_name='jobs')
    op.drop_table('jobs')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')