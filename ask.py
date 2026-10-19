


import sys


def main():
 
 foldername = sys.argv[1]
 question = " ".join(sys.argv[2:])

 folder = Path(foldername)
 chunks = []

 documents = read_folder(folder)

 for document in documents:
     for chunk in chunk_text(document["text"]):
         chunks.append({
             "file": document["file"],
             "chunk": chunk
         })
 relevant_chunks = get_relevant_chunks(chunks, question)
 chunkss = "\n".join(relevant_chunks)        



 prompt = f"Answer the question using this context: {chunkss} and here is my question: {question}"

 
 answer = ask_llm(prompt)

 print(answer)


if __name__ == "__main__":
  main()