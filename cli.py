
import sys
from pathlib import Path
from memory import remember_note, recall_notes
from reader import read_folder, chunk_text, get_relevant_chunks
from llm import ask_llm


def main():
    foldername = sys.argv[1]
    if len(sys.argv) >= 4 and sys.argv[1] == "remember":
     project = sys.argv[2]
     note = " ".join(sys.argv[3:])
     remember_note(project, note)
     return
    
    if len(sys.argv) >= 4 and sys.argv[1] == "recall":
     project = sys.argv[2]
     question = " ".join(sys.argv[3:])
     matches = recall_notes(project, question)

     
     
     used_notes = []

     for match in matches[:5]:
       note = match["metadata"].get("text", "").strip()

       if not note:
              continue

       if len(note) > 500:
              note = note[:500].rstrip() + "..."

       used_notes.append(note)

     memories = "\n".join(used_notes)


     print(f"\nProject: {project}")
     print(f"Memory notes used: {len(used_notes)}")

     for i, note in enumerate(used_notes, start=1):
      preview = note[:100].replace("\n", " ")
      print(f"{i}. {preview}")
     
     prompt = (
     f"Use these project memories if relevant:\n{memories}\n\n"
     f"Question: {question}"
     )

     ask_llm(prompt)
     return
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
    chunkss = relevant_chunks

    prompt = f"Answer the question using this context: {chunkss} and here is my question: {question}"

    
    project = folder.name

    try:
     answer = ask_llm(prompt)
    except Exception as error:
        print(f"Couldnt get an ans: {error}")
        return

    if answer.strip():

     summary_prompt = f"""
     Summarize this agent run in exactly 2 short lines.

     Question asked:
     {question}

     Answer given:
     {answer}

     Capture the main finding or decision.
     Do not invent facts. Be concise.
     Return only the 2-line summary.
     """
     try:  
      summary = ask_llm(summary_prompt)

      if summary.strip():
       remember_note(project, summary)
       print("Run summary saved to project memory.")
       
     except Exception as error:
      print(f"Couldnt get a summary: {error}") 


if __name__ == "__main__":
    main()
