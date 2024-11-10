# llm/document_retrieval.py

import pinecone
from langchain.prompts import PromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.output_parsers import JsonOutputParser
from utils.config import llm, pc, tavily, get_azure_openai_embedding
from core.state import GraphState

def retrieve_similar_docs(state: GraphState) -> GraphState:
    print("RETRIEVING DOCUMENTS")

    cve_queries = state["cve_queries"]
    all_similar_docs = [[] for _ in range(len(cve_queries))]  # Initialize a 2D array
    
    index_name = "azure-specific-test"
    index = pc.Index(index_name)

    for i, query in enumerate(cve_queries):

        query_embedding = get_azure_openai_embedding(query)

        similar_docs_by_embedding = index.query(top_k=1, include_metadata=True, vector=query_embedding)
        
        all_similar_docs[i] = similar_docs_by_embedding['matches']
        
        cve_id = state["cve_ids"][i]  # Assuming cve_ids and cve_queries are aligned
        try:
            doc_by_id = index.fetch(ids=[cve_id])
            if doc_by_id and cve_id in doc_by_id['vectors']:
                doc_data = doc_by_id['vectors'][cve_id]
                doc_data['values'] = []
                all_similar_docs[i].append(doc_data)
        except Exception as e:
            print(f"Error retrieving document by ID {cve_id}: {e}")

    state["similar_docs"] = all_similar_docs
    state["steps"].append("retrieve_similar_docs")
    return state

def grade_documents(state: GraphState) -> GraphState:
    print("GRADING DOCUMENTS")
    """
    Grade the relevance of retrieved documents.
    """
    cve_queries = state["cve_queries"]
    all_filtered_docs = [[] for _ in range(len(cve_queries))]

    prompt = PromptTemplate(
        template="""You are a teacher grading a quiz. You will be given: 
        1/ a QUESTION
        2/ A FACT provided by the student
        
        You are grading RELEVANCE RECALL:
        A score of 1 means that ANY of the statements in the FACT are relevant to the QUESTION. 
        A score of 0 means that NONE of the statements in the FACT are relevant to the QUESTION. 
        1 is the highest (best) score. 0 is the lowest score you can give. 
        
        Explain your reasoning in a step-by-step manner. Ensure your reasoning and conclusion are correct. 
        
        Avoid simply stating the correct answer at the outset.
        
        Question: {question} \n
        Fact: \n\n {documents} \n\n
        
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
        Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.
        """,
        input_variables=["question", "documents"],
    )

    retrieval_grader = prompt | llm | JsonOutputParser()

    for i, query in enumerate(cve_queries):
        documents = state["similar_docs"][i]
        filtered_docs = []

        for doc in documents:
            doc_text = doc['metadata']['text']
            score = retrieval_grader.invoke({"question": query, "documents": doc_text})
            if score["score"] == 1:
                filtered_docs.append(doc)

        all_filtered_docs[i] = filtered_docs

    state["filtered_docs"] = all_filtered_docs
    state["steps"].append("grade_documents")
    return state

def augment_with_web_search(state: GraphState) -> GraphState:
    print("SEARCHING WEB")
    """
    Augment the filtered documents with web search results if any CVE ID has fewer than 2 documents.
    """
    cve_queries = state["cve_queries"]
    filtered_docs = state["filtered_docs"]
    augmented_docs = [[] for _ in range(len(cve_queries))]

    for i, docs in enumerate(filtered_docs):
        augmented_docs[i] = docs.copy()

        if len(docs) < 2:
            query = cve_queries[i]
            additional_docs = tavily.invoke({"query": query})

            if isinstance(additional_docs, list):
                for result in additional_docs:
                    doc = {
                        "metadata": {
                            "text": result.get("content", ""),
                            "url": result.get("url", "")
                        }
                    }
                    augmented_docs[i].append(doc)

            if len(augmented_docs[i]) < 2:
                print(f"Warning: CVE ID {cve_queries[i]} still has fewer than 2 documents after web search.")
        
    state["augmented_docs"] = augmented_docs
    state["steps"].append("augment_with_web_search")
    return state

def answer_cve_queries_and_augment_docs(state: GraphState) -> GraphState:
    print("SELF AUGMENTING")
    """
    Answers each query in the list of CVE queries using GPT and appends the answer to the corresponding sublist in augmented_docs.
    """
    cve_queries = state["cve_queries"]
    augmented_docs = state["augmented_docs"]

    for i, query in enumerate(cve_queries):
        prompt_template = PromptTemplate(
            template="""
            Please provide a detailed answer to the following question:

            {query}
            """,
            input_variables=["query"]
        )

        final_prompt = prompt_template.format(query=query)
        response = llm.invoke(final_prompt)

        doc_entry = {
            "metadata": {
                "text": response.content,
                "source": "GPT-Generated Answer"
            }
        }

        augmented_docs[i].append(doc_entry)

    state["augmented_docs"] = augmented_docs
    state["steps"].append("answer_cve_queries_and_augment_docs")
    return state
