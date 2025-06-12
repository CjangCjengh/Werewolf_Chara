# import logging

# # Configure your logger
# logger = logging.getLogger('my_app_logger')
# logger.setLevel(logging.DEBUG)

# BLUE = '\033[94m'
# RESET = '\033[0m'

# # Custom formatter to add indentation and blue color to log messages
# class IndentFormatter(logging.Formatter):
#     def format(self, record):
#         # Indent each line of the log message and add blue color
#         indented_message = '    ' + record.getMessage().replace('\n', '\n    ')
#         colored_message = f"{BLUE}{indented_message}{RESET}"
#         return colored_message
    
# handler = logging.StreamHandler()
# handler.setFormatter(IndentFormatter())
# logger.addHandler(handler)

# # Prevent the logger from propagating messages to the root logger
# logger.propagate = False

# # Function to print logger configuration for debugging
# def print_logger_configuration():
#     root_logger = logging.getLogger()
#     print("Root Logger Handlers:")
#     for handler in root_logger.handlers:
#         print(f" - {handler}")

#     loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
#     for logger in loggers:
#         print(f"\nLogger: {logger.name}")
#         if logger.handlers:
#             for handler in logger.handlers:
#                 print(f" - {handler}")
#         else:
#             print(" - No handlers")

# # Clean up root logger handlers if necessary
# for handler in logging.getLogger().handlers:
#     logging.getLogger().removeHandler(handler)

# # Print configuration to verify
# print_logger_configuration()

# # Suppress logging for all external loggers to WARNING level or higher
# for logger_name in logging.root.manager.loggerDict:
#     if logger_name != 'my_app_logger':  # Skip your custom logger
#         logging.getLogger(logger_name).setLevel(logging.WARNING)

# # Example usage
# logger.info("Game Start.")

logger = None