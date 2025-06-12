# import openai
# import gradio as gr
# from time import sleep
# # 
# # Define the API clients
# client_glm = openai.OpenAI(api_key="ea2a21b005e44c0fe0f6601641fcb12b.aZLdLAUWHa6azlyI", base_url="https://open.bigmodel.cn/api/paas/v4/")
# message_history = []




# def call_api():
#     messages = [{"role": "system", "content": "You are a helpful assistant."}]
#     for user_message in message_history:
#         if user_message.strip():  # Ensure message content is not empty
#             messages.append({"role": "user", "content": user_message})
#     import ipdb;ipdb.set_trace()
#     # Ensure that messages list meets the API requirements
#     if not messages[-1].get("content"):
#         messages[-1]["content"] = "."

#     while True:
#         try:
#             response = client_glm.chat.completions.create(
#                 model="glm-3-turbo",
#                 messages=messages
#             )
#             assistant_message = response.choices[0].message.content
#         except Exception as e:
#             print(f"Error: {e}")
#             sleep(1.5)
#         else:
#             break
#     return assistant_message

# # Define the Gradio ChatInterface
# iface = gr.ChatInterface(
#     fn=call_api,
#     title="Chat with GPT-3.5",
#     description="Type a message and chat with OpenAI's models via different APIs."
# )

# # Launch the interface with public sharing enabled
# iface.launch(share=True)


import gradio as gr
import openai
client_glm = openai.OpenAI(api_key="ea2a21b005e44c0fe0f6601641fcb12b.aZLdLAUWHa6azlyI", base_url="https://open.bigmodel.cn/api/paas/v4/")


def call_api(self, message):
    while True:
        try:
            response = self.client_glm.chat.completions.create(
                model="glm-3-turbo",
                messages=message
            )
            assistant_message = response.choices[0].message.content
        except Exception as e:
            # print("e", end="")
            print(f"Error: {e}")
            # print(f"Error: {e}")
            # sleep(1.5)
        else:
            break
    return assistant_message


def echo(message, history):
    # Append the user message and bot response to the history
    history.append([message])
    
    return message

demo = gr.ChatInterface(fn=echo, examples=["hello", "hola", "merhaba"], title="Echo Bot")
demo.launch()
