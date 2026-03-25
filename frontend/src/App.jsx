import { useMemo, useState } from "react";
import { askQuestion, uploadPdf } from "./api";

const EXAMPLE_QUESTIONS = [
  "What medications is the patient taking?",
  "Summarize discharge notes for this patient.",
  "What allergies are documented in the clinical notes?",
];

function UploadCard({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setMessage("");
    try {
      const payload = await uploadPdf(file);
      onUploaded(payload);
      setMessage(`Uploaded ${payload.filename} (${payload.chunks_created} chunks)`);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-white">Upload Healthcare PDF</h2>
      <p className="mt-1 text-sm text-slate-400">
        Upload patient records, discharge summaries, clinical notes, or compliance files.
      </p>
      <div className="mt-3 flex flex-col gap-3">
        <input
          type="file"
          accept=".pdf,application/pdf"
          className="block w-full text-sm text-slate-300 file:mr-4 file:rounded-md file:border-0 file:bg-cyan-600 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-cyan-500"
          onChange={(event) => setFile(event.target.files?.[0] || null)}
        />
        <button
          className="rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 disabled:cursor-not-allowed disabled:bg-slate-700"
          disabled={!file || loading}
          onClick={handleUpload}
        >
          {loading ? "Uploading..." : "Upload Document"}
        </button>
      </div>
      {message && <p className="mt-3 text-sm text-slate-300">{message}</p>}
    </div>
  );
}

function QueryComposer({ onSubmit, loading }) {
  const [question, setQuestion] = useState("");

  const submit = async () => {
    if (!question.trim()) return;
    await onSubmit(question.trim());
    setQuestion("");
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-white">Clinical Q&A</h2>
      <div className="mt-3 flex gap-2">
        <input
          className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
          placeholder="Ask a question about patient records..."
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") submit();
          }}
        />
        <button
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-slate-700"
          disabled={loading || !question.trim()}
          onClick={submit}
        >
          {loading ? "Analyzing..." : "Ask"}
        </button>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {EXAMPLE_QUESTIONS.map((sample) => (
          <button
            key={sample}
            className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:border-cyan-500 hover:text-cyan-300"
            onClick={() => setQuestion(sample)}
            type="button"
          >
            {sample}
          </button>
        ))}
      </div>
    </div>
  );
}

function SourcesPanel({ chunks }) {
  if (!chunks?.length) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-400">
        Source chunks appear here after each answer.
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-cyan-300">Retrieved Sources</h3>
      <div className="mt-3 space-y-3">
        {chunks.map((chunk, index) => (
          <div key={`${chunk.source}-${chunk.chunk_id}-${index}`} className="rounded-md border border-slate-700 bg-slate-950 p-3">
            <div className="mb-2 flex flex-wrap gap-2 text-xs text-slate-400">
              <span className="rounded bg-slate-800 px-2 py-1">{chunk.source}</span>
              <span className="rounded bg-slate-800 px-2 py-1">Chunk #{chunk.chunk_id}</span>
              <span className="rounded bg-slate-800 px-2 py-1">Similarity: {chunk.similarity ?? "n/a"}</span>
            </div>
            <p className="text-sm leading-6 text-slate-200">{chunk.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChatPanel({ messages }) {
  const hasMessages = messages.length > 0;
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-white">Conversation</h2>
      <div className="mt-3 space-y-4">
        {!hasMessages && <p className="text-sm text-slate-400">No messages yet. Upload PDFs and ask a question.</p>}
        {messages.map((message) => (
          <div key={message.id} className="space-y-2">
            <div className="rounded-md border border-cyan-700 bg-cyan-950/40 p-3 text-sm text-cyan-50">
              <strong className="mr-2">You:</strong>
              {message.question}
            </div>
            <div className="rounded-md border border-emerald-700 bg-emerald-950/40 p-3 text-sm text-emerald-50">
              <div>
                <strong className="mr-2">Assistant:</strong>
                {message.answer}
              </div>
              <div className="mt-2 text-xs text-emerald-200">Response time: {message.responseTimeMs} ms</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [uploads, setUploads] = useState([]);
  const [messages, setMessages] = useState([]);
  const [latestSources, setLatestSources] = useState([]);
  const [loading, setLoading] = useState(false);

  const uploadedCount = useMemo(() => uploads.length, [uploads.length]);

  const onSubmitQuestion = async (question) => {
    setLoading(true);
    try {
      const payload = await askQuestion(question);
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-${current.length}`,
          question,
          answer: payload.answer,
          responseTimeMs: payload.response_time_ms,
        },
      ]);
      setLatestSources(payload.retrieved_chunks || []);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-${current.length}`,
          question,
          answer: `Error: ${error.message}`,
          responseTimeMs: 0,
        },
      ]);
      setLatestSources([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 md:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-xl border border-slate-800 bg-gradient-to-r from-slate-900 to-slate-800 p-6">
          <h1 className="text-2xl font-bold text-white md:text-3xl">Healthcare Document Intelligence System</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-300">
            Domain-specific RAG assistant for patient records, clinical summaries, and compliance documents.
            Upload care documents, ask natural-language questions, and inspect grounded source evidence.
          </p>
          <p className="mt-2 text-xs text-cyan-300">Indexed files this session: {uploadedCount}</p>
        </header>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-1">
            <UploadCard onUploaded={(payload) => setUploads((prev) => [...prev, payload])} />
            <QueryComposer onSubmit={onSubmitQuestion} loading={loading} />
          </div>
          <div className="space-y-6 lg:col-span-2">
            <ChatPanel messages={messages} />
            <SourcesPanel chunks={latestSources} />
          </div>
        </div>
      </div>
    </main>
  );
}
