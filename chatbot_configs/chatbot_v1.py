def generate_response(client, chat_history):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=chat_history
    )
    return response.choices[0].message.content
