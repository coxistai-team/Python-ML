# from transformers import pipeline

# classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
# non_edu_keywords = ["movie", "netflix", "watch", "download", "shopping", "travel","celebrity","repair my", "fix my", "broken", "not working", 
#         r"which.*best","how much to repair", "where to fix","price of", "how much does", "cost of","which phone", "which mobile","which game", "best ice cream","recommend a", "which brand", "better option", "should I buy", "top rated", "which.*best"]
# edu_keywords = ["explain", "why", "how", "science", "language", "history", "logic","architecture", "design principles", "engineering","teach me", "learning", "pedagogy","types of", "list of", "classification of", 
#                 "define", "what is", "difference between"]

# def is_educational(question):
#     if any(keyword in question.lower() for keyword in non_edu_keywords):
#         return False
    
#     if any(keyword in question.lower() for keyword in edu_keywords):
#         return True

    
#     labels = [
#         # "academic, general knowledge, critical thinking, language, or science",
#         # "movies, shopping, travel, or personal lifestyle"
#         # "educational,science, biology, agriculture, general knowledge, or facts,requesting knowledge, academic explanation, technology, coding ,general knowledge, critical thinking, language, science ,maths,or skill development",
#         # "asking about prices, personal technical support, shopping, or entertainment"
#        "educational: seeks factual knowledge, explanations, technology, critical thinking, science,maths,sports,coding,or academic concepts",
#         # "non-educational: requests opinions, recommendations, gaming, shopping, or personal preferences"
#         "non-educational: requests product comparisons, Consumer_Product_Advice,shopping advice, entertainment, gaming, or personal opinions"
        
#     ]
#     result = classifier(question, labels)

#     return result["scores"][0] > 0.85

# # Test
# questions =[
#     "what is your favourite meal and who makes it best"
#     ]
# for q in questions:
#     print(f"Q: {q}")
#     print("Educational" if is_educational(q) else "Non-educational")
#     print("---")


from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
non_edu_keywords = ["movie", "theft","robbery", "netflix", "watch", "download", "shopping", "travel", "celebrity", "repair my", "fix my", "broken", "not working", 
        "how much to repair", "where to fix", "price of", "how much does", "cost of", "which phone", "which mobile", "which game", "best ice cream", "TalkingToPlants", "recommend a", "which brand", "better option", "should I buy", "top rated", "which.*best"]
edu_keywords = ["explain", "how", "science", "language", "history", "scientific", "logic", "architecture", "design principles", "engineering", "teach me", "learning", "pedagogy", "types of", "list of", "classification of", 
                "define", "difference between"]

def is_educational(question):
    if any(keyword in question.lower() for keyword in non_edu_keywords):
        return False
    
    if any(keyword in question.lower() for keyword in edu_keywords):
        return True

    
    labels = [
        
       "educational: factual knowledge, explanations, technology, critical thinking, science, maths, sports, coding, general knowledge, or academic concepts",
        "non-educational: requests product comparisons, unsafe, Consumer Product Advice, shopping advice, entertainment,random_fun, plant_motivation, absurd_request, gaming, or personal opinions"
        
    ]
    result = classifier(question, labels)

    return result["scores"][0] > 0.85

