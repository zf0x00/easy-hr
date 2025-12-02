
import {
  PromptInput,
  PromptInputAttachment,
  PromptInputAttachments,
  PromptInputBody,
  PromptInputFooter,
  type PromptInputMessage,
  PromptInputProvider,
  PromptInputSpeechButton,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
  usePromptInputController,
} from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import { api } from "@/lib/api";
import { CheckIcon, GlobeIcon } from "lucide-react";
import { useRef, useState } from "react";
import ResultCard, { parseLLMResponse } from "./ResultCard";

const models = [
  {
    id: "gpt-4o",
    name: "GPT-4o",
    chef: "OpenAI",
    chefSlug: "openai",
    providers: ["openai", "azure"],
  },
  {
    id: "gpt-4o-mini",
    name: "GPT-4o Mini",
    chef: "OpenAI",
    chefSlug: "openai",
    providers: ["openai", "azure"],
  },
  {
    id: "claude-opus-4-20250514",
    name: "Claude 4 Opus",
    chef: "Anthropic",
    chefSlug: "anthropic",
    providers: ["anthropic", "azure", "google", "amazon-bedrock"],
  },
  {
    id: "claude-sonnet-4-20250514",
    name: "Claude 4 Sonnet",
    chef: "Anthropic",
    chefSlug: "anthropic",
    providers: ["anthropic", "azure", "google", "amazon-bedrock"],
  },
  {
    id: "gemini-2.0-flash-exp",
    name: "Gemini 2.0 Flash",
    chef: "Google",
    chefSlug: "google",
    providers: ["google"],
  },
];

const SUBMITTING_TIMEOUT = 200;
const STREAMING_TIMEOUT = 2000;

const HeaderControls = () => {
  const controller = usePromptInputController();

  return (
    <header className="mt-8 flex items-center justify-between">
      <p className="text-sm">
        Header Controls via{" "}
        <code className="rounded-md bg-muted p-1 font-bold">
          PromptInputProvider
        </code>
      </p>
      <ButtonGroup>
        <Button
          onClick={() => {
            controller.textInput.clear();
          }}
          size="sm"
          type="button"
          variant="outline"
        >
          Clear input
        </Button>
        <Button
          onClick={() => {
            controller.textInput.setInput("Inserted via PromptInputProvider");
          }}
          size="sm"
          type="button"
          variant="outline"
        >
          Set input
        </Button>

        <Button
          onClick={() => {
            controller.attachments.clear();
          }}
          size="sm"
          type="button"
          variant="outline"
        >
          Clear attachments
        </Button>
      </ButtonGroup>
    </header>
  );
};

const PromptInputComponent = ({ onNewChat, showResults = true }: { onNewChat?: (messages: any[]) => void, showResults?: boolean }) => {
  const [status, setStatus] = useState<
    "submitted" | "streaming" | "ready" | "error"
  >("ready");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [parsedCandidates, setParsedCandidates] = useState<any[]>([]);
  
  const handleSubmit = async (message: PromptInputMessage) => {
    const hasText = Boolean(message.text);
    const hasAttachments = Boolean(message.files?.length);

    if (!(hasText || hasAttachments)) {
      return;
    }

    try {
      setStatus("submitted");
      setParsedCandidates([]); // Clear previous results
      
      const res = await api.post("/search", { query: message.text });
      const candidates = res.data.result; // This is now an array of candidate objects
      
      setParsedCandidates(candidates);
      
      if (onNewChat) {
        const messages = [
          { role: 'user', content: message.text },
          // Stringify candidates for storage in chat history
          { role: 'assistant', content: JSON.stringify(candidates, null, 2) },
        ];
        onNewChat(messages);
      }
      
      setStatus("streaming");
      
      setTimeout(() => {
        setStatus("ready");
      }, SUBMITTING_TIMEOUT);
      
    } catch (error) {
      console.error("Search failed:", error);
      setStatus("error");
      
      setTimeout(() => {
        setStatus("ready");
      }, 3000);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {showResults && parsedCandidates.length > 0 && (
        <div className="mt-8 space-y-4">
          <h3 className="text-lg font-semibold text-center">
            Found {parsedCandidates.length} matching candidates
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {parsedCandidates.map((candidate, index) => (
              <ResultCard
                key={candidate.id || index}
                candidate={candidate}
                index={index}
              />
            ))}
          </div>
        </div>
      )}

      <PromptInputProvider>
        <PromptInput globalDrop multiple onSubmit={handleSubmit}>
          <PromptInputAttachments>
            {(attachment) => <PromptInputAttachment data={attachment} />}
          </PromptInputAttachments>
          <PromptInputBody>
            <PromptInputTextarea ref={textareaRef} />
          </PromptInputBody>
          <PromptInputFooter>
            <PromptInputTools>
              <PromptInputSpeechButton textareaRef={textareaRef} />
            </PromptInputTools>
            <PromptInputSubmit status={status} />
          </PromptInputFooter>
        </PromptInput>
      </PromptInputProvider>
    </div>
  );
};

export default PromptInputComponent;
