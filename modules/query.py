import os
from typing import Optional
from openai import OpenAI
from datetime import datetime

class SmartDeepSeek:
    """
    A class to interact with the OpenAI API, which intelligently selects
    a model based on query complexity or user dissatisfaction.
    """
    def __init__(self, api_key: Optional[str] = None):
        """Initializes the OpenAI client and sets up model tiers."""
        # Load API key from argument or environment variable
        if api_key is None:
            api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set. Please add it to your .env file.")
        self.client = OpenAI(api_key=api_key)

        # Model tiers
        self.free_model = "gpt-3.5-turbo"
        self.paid_model = "gpt-4o"
        self.reason_model = "gpt-4-turbo"

        # Application-specific logic for model switching
        self.complexity_threshold = 15  # Word count
        self.dissatisfaction_triggers = [
            "not satisfied", "explain better",
            "more detail", "incomplete answer"
        ]

    def needs_paid_model(self, question: str, previous_response: str = "") -> bool:
        """Determines if a question requires a more advanced model."""
        question_lower = question.lower()

        # Trigger if the user is dissatisfied with a previous response
        if any(trigger in previous_response.lower() for trigger in self.dissatisfaction_triggers):
            return True

        # Trigger for long, complex questions
        if len(question.split()) > self.complexity_threshold:
            return True

        # Trigger for questions that ask for detailed analysis
        technical_terms = [
            "explain in detail", "step-by-step",
            "prove that", "compare and contrast"
        ]
        if any(term in question_lower for term in technical_terms):
            return True

        return False

    def query_model(self, model: str, question: str) -> Optional[str]:
        """Queries the specified model using the OpenAI client with custom prompts."""
        prompts = {
            self.free_model: f"Provide a helpful response to: {question}",
            self.paid_model: f"As an expert, analyze this in depth:\n{question}\nInclude examples and practical applications.",
            self.reason_model: f"Perform rigorous step-by-step analysis:\n1. Problem: {question}\n2. Key components\n3. Logical relationships\n4. Final synthesized answer"
        }

        # Use the specific prompt or the original question as a fallback
        prompt_content = prompts.get(model, question)

        try:
            # Use the OpenAI client to create a chat completion
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0.5
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"API Error for model '{model}': {e}")
            return None

    def get_response(self, question: str, previous_response: str = "") -> str:
        """Determines the best model and gets a response."""
        model_to_use = self.free_model
        if self.needs_paid_model(question, previous_response):
            print("--> Complex query detected. Using paid model.")
            model_to_use = self.paid_model
        else:
            print("--> Simple query detected. Using free model.")

        response = self.query_model(model_to_use, question)

        # Fallback to the reason_model if the paid_model fails
        if model_to_use == self.paid_model and not response:
            print("--> Fallback: Trying the reason_model...")
            response = self.query_model(self.reason_model, question)

        return response or "I couldn't generate a response for this question."


# --- Example Usage ---
if __name__ == "__main__":
    # Best practice: Load the API key from an environment variable
    API_KEY = os.getenv("OPENROUTER_API_KEY")

    if not API_KEY:
        print("Error: Please set your OPENROUTER_API_KEY in the environment variables.")
    else:
        assistant = SmartDeepSeek(api_key=API_KEY)

        # --- Test Case 1: Simple Question ---
        print("\n--- Query 1: Simple Question ---")
        q1 = "Who is the current Chief Minister of Telangana?"
        response1 = assistant.get_response(q1)
        print(f"Q: {q1}\nA: {response1}")

        # --- Test Case 2: Complex Question triggering the paid model ---
        print("\n--- Query 2: Complex Question ---")
        q2 = "Explain in detail the key differences between nuclear fission and fusion."
        response2 = assistant.get_response(q2)
        print(f"Q: {q2}\nA: {response2}")

        # --- Test Case 3: Dissatisfaction triggering the paid model ---
        print("\n--- Query 3: Follow-up with Dissatisfaction ---")
        previous_simple_response = "Photosynthesis is how plants make food."
        q3 = "That's an incomplete answer, I need more detail about the two main stages."
        response3 = assistant.get_response(q3, previous_response=previous_simple_response)
        print(f"Q: {q3}\nA: {response3}")