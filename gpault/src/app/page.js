import ChatInput from "./components/ChatInput";
import MessageField from "./components/MessageField";
import ModelDropdown from "./components/ModelDropdown";

export default function Home() {
  return (
    <>
      <div className="min-h-screen bg-slate-50">
        <h1 className="py-16 text-lg font-semibold text-center">
          G<span className="text-green-600">P</span>aulT
        </h1>
        <div className="max-w-5xl flex gap-8 mx-auto">
          <div className="w-3/4">
            <MessageField />
            <ChatInput />
          </div>
          <div className="w-1/4">
            <ModelDropdown />
          </div>
        </div>
      </div>
    </>
  );
}
