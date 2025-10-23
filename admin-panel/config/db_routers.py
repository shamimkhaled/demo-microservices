class DatabaseRouter:
    """
    Database router to handle multiple database connections
    """
    route_app_labels = {
        'users': 'auth_db',
        'roles': 'auth_db',
        'authentication': 'auth_db',
        'organizations': 'organization_db',
    }

    def db_for_read(self, model, **hints):
        app_label = model._meta.app_label
        if app_label in self.route_app_labels:
            return self.route_app_labels[app_label]
        return 'default'

    def db_for_write(self, model, **hints):
        app_label = model._meta.app_label
        if app_label in self.route_app_labels:
            return self.route_app_labels[app_label]
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == self.route_app_labels[app_label]
        return db == 'default'