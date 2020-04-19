class Task:

    def __init__(self):
        self.task_f = {}

    def task(self, task_name):
        def decorator(f):
            self.task_f[task_name] = f
            return f

        return decorator

    def resolve(self, task_name, content, client):
        if task_name not in self.task_f:
            return print(f"TASK [{task_name}] HANDLING NOT IMPLEMENTED IGNORED")
        print(self.task_f[task_name])
        return self.task_f[task_name]("foo", content, client)

task = Task()