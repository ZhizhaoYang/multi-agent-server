
class Logger:
    def __init__(self):
        pass

    def log_info(self, message: str):
        print(f"**** [INFO] {message} ****")

    def log_error(self, message: str):
        print(f"**** [ERROR] {message} ****")

    def log_warning(self, message: str):
        print(f"**** [WARNING] {message} ****")

    def log_debug(self, message: str):
        print(f"**** [DEBUG] {message} ****")

    def log_node(self, message: str):
        print(f"**** [NODE] {message} ****")

    def log_edge(self, message: str):
        print(f"**** [EDGE] {message} ****")



