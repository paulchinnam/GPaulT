export default function ChatInput() {
  return (
    <>
      <div className="mt-4 flex gap-4">
        <textarea
          rows={4}
          name="comment"
          id="comment"
          placeholder="Enter your message here"
          className="pl-2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-green-600 sm:text-sm sm:leading-6"
          defaultValue={""}
        />
        <button
          type="button"
          className="h-fit rounded-md bg-green-600 px-9 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600"
        >
          Send
        </button>
      </div>
    </>
  );
}
