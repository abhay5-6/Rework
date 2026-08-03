import { useState } from "react";
import { Search, Loader } from "lucide-react";
import { searchRoom, queryRoom, SearchResult } from "@/lib/api/ai";

const PREBUILT_QUERIES = [
  "What decisions have we made?",
  "What are current tasks?",
  "Summarize this room",
  "What are unresolved bugs?",
  "What is the architecture?",
  "Key learnings and insights",
];

export default function AISearchTab({ roomId }: { roomId: number }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult | null>(null);
  const [answer, setAnswer] = useState<string | null>(null);
  const [showPrebuilt, setShowPrebuilt] = useState(false);

  async function handleSearch() {
    if (!query.trim()) return;
    try {
      setLoading(true);
      setAnswer(null);
      const result = await searchRoom(roomId, query);
      setResults(result);
      const aiAnswer = await queryRoom(roomId, query);
      setAnswer(aiAnswer.answer);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  function handlePrebuiltQuery(q: string) {
    setQuery(q);
    setShowPrebuilt(false);
  }

  return (
    <>
      <div className="space-y-3">
        <div className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
            placeholder="Ask anything..."
            className="flex-1 bg-muted border border-border rounded-xl px-4 py-2 text-foreground placeholder-zinc-500 outline-none focus:border-blue-500 transition"
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-foreground p-2 rounded-xl transition"
          >
            {loading ? <Loader size={18} className="animate-spin" /> : <Search size={18} />}
          </button>
        </div>

        <div className="relative">
          <button
            onClick={() => setShowPrebuilt(!showPrebuilt)}
            className="w-full text-sm text-muted-foreground hover:text-foreground transition py-2 text-left"
          >
            💡 Suggestions
          </button>
          {showPrebuilt && (
            <div className="absolute top-full left-0 right-0 bg-muted border border-border rounded-xl mt-2 p-2 space-y-1 z-50">
              {PREBUILT_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => handlePrebuiltQuery(q)}
                  className="w-full text-left text-sm text-foreground hover:bg-card p-2 rounded-lg transition"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {results && (
        <div className="space-y-4">
          {answer && (
            <div className="bg-blue-900/20 border border-blue-700/30 rounded-xl p-4 space-y-2">
              <h3 className="text-sm font-semibold text-blue-300">Answer</h3>
              <p className="text-sm text-foreground leading-relaxed">{answer}</p>
            </div>
          )}
          {results.memories.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">
                📚 Memories ({results.memories.length})
              </h3>
              <div className="space-y-2">
                {results.memories.map((memory) => (
                  <div key={memory.id} className="bg-muted/50 border border-border rounded-lg p-3">
                    <div className="text-xs text-muted-foreground mb-1">{memory.memory_type}</div>
                    <p className="text-sm text-foreground line-clamp-2">{memory.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {results.messages.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">
                💬 Messages ({results.messages.length})
              </h3>
              <div className="space-y-2">
                {results.messages.map((msg) => (
                  <div key={msg.id} className="bg-muted/50 border border-border rounded-lg p-3">
                    <div className="text-xs text-muted-foreground mb-1">
                      Score: {msg.score.toFixed(2)}
                    </div>
                    <p className="text-sm text-foreground line-clamp-2">{msg.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!results && !loading && (
        <div className="text-center text-muted-foreground text-sm py-8">
          Search for memories, messages, or ask questions
        </div>
      )}
    </>
  );
}
