"""Migration de l'id de prospect en UUID

Revision ID: dfa36a0200c8
Revises: 
Create Date: 2025-08-18 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'dfa36a0200c8' # Laisse ton ID unique ici
down_revision = None # Laisse ton ID précédent ici
branch_labels = None
depends_on = None

def upgrade() -> None:

    # Étape 0 : Créer l'extension UUID si elle n'existe pas
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Étape 1 : Ajouter une nouvelle colonne temporaire de type UUID
    op.add_column('prospects', sa.Column('uuid_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Étape 2 : Peupler la nouvelle colonne avec des UUID générés
    op.execute("UPDATE prospects SET uuid_id = uuid_generate_v4()")

    # Étape 3 : Supprimer l'ancienne colonne et ses contraintes
    # op.drop_constraint('ix_prospects_id', 'prospects', type_='unique')
    op.drop_column('prospects', 'id')

    # Étape 4 : Renommer la nouvelle colonne et la configurer comme la nouvelle clé primaire
    op.alter_column('prospects', 'uuid_id', new_column_name='id', nullable=False)
    op.create_primary_key('pk_prospects', 'prospects', ['id'])
    
    # Nous devons aussi recréer l'index sur 'id' qui a été supprimé
    op.create_index('ix_prospects_id', 'prospects', ['id'])

def downgrade() -> None:
    # Pour revenir en arrière, c'est plus compliqué car nous ne pouvons pas
    # re-créer les ID originaux. Nous allons simplement recréer l'ancienne
    # colonne avec des valeurs par défaut pour que la migration passe.
    
    # D'abord, supprime les contraintes
    op.drop_constraint('pk_prospects', 'prospects', type_='primary')
    op.drop_index('ix_prospects_id', 'prospects')

    # Ajoute l'ancienne colonne et supprime la nouvelle
    op.add_column('prospects', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_column('prospects', 'uuid_id')
    
    # Ajoute les contraintes sur l'ancienne colonne
    op.create_unique_constraint('ix_prospects_id', 'prospects', ['id'])
    op.create_primary_key('pk_prospects', 'prospects', ['id'])
