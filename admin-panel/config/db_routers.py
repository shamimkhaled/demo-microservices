"""
Database Router for Unified Admin Panel
Routes models from different services to their respective databases
"""

class ServiceDatabaseRouter:
    """
    Routes models to their respective service databases:
    - Auth service models (users, roles, authentication) → auth_db
    - Organization service models → org_db
    - Admin panel models → default
    """

    def db_for_read(self, model, **hints):
        """Direct reads to appropriate database"""
        if model._meta.app_label in ['users', 'roles', 'authentication']:
            return 'auth_db'
        elif model._meta.app_label in ['organizations']:
            return 'org_db'
        return 'default'

    def db_for_write(self, model, **hints):
        """Direct writes to appropriate database"""
        if model._meta.app_label in ['users', 'roles', 'authentication']:
            return 'auth_db'
        elif model._meta.app_label in ['organizations']:
            return 'org_db'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both models are in the same database"""
        db1 = self.db_for_read(type(obj1))
        db2 = self.db_for_read(type(obj2))
        if db1 == db2:
            return True
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Ensure each app's migrations run on its database:
        - auth service apps migrate to auth_db
        - org service apps migrate to org_db
        - admin panel apps migrate to default
        """
        if app_label in ['users', 'roles', 'authentication']:
            return db == 'auth_db'
        elif app_label in ['organizations']:
            return db == 'org_db'
        return db == 'default'