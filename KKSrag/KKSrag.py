from langchain.chat_models import init_chat_model


class KKSRag:
    def __init__(self, base_url: str, model: str, api_key: str):
        self.model = init_chat_model(
            base_url=base_url,
            model=model,
            api_key=api_key,
        )

    def Ragresponse(self, question: str, context: str, stream: bool = True):
        GENERATE_PROMPT = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer the question. "
            "If you don't know the answer, just say that you don't know. "
            "Use three sentences maximum and keep the answer concise.\n"
            "Question: {question} \n"
            "Context: {context}"
        )
        prompt = GENERATE_PROMPT.format(question=question, context=context)
        
        if stream:
            response = self.model.stream(prompt)
        else:
            response = self.model.invoke(prompt)
        
        return response



    def Answer(self, question: str, context: str):
        PROMPT = "你是一名考生，我现在是提问老师，请简要回答我的问题。{question}"
        prompt = PROMPT.format(question=question)
        response = self.Ragresponse(prompt, context)
        return response
