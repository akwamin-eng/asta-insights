import { useState } from "react";
import { useRouter } from "next/router";

export default function LazyListingForm() {
  const [files, setFiles] = useState([]);
  const [price, setPrice] = useState("");
  const [hint, setHint] = useState("");
  const [status, setStatus] = useState("idle"); // idle, uploading, success, error
  const [progressMsg, setProgressMsg] = useState("");
  const router = useRouter();

  // The "Transparency" Animation
  const startProgressSimulation = () => {
    const messages = [
      "📉 Compressing images (Data Saver)...", // 0s
      "🛰️ Triangulating GPS Location...", // 1.5s
      "🧠 AI is analyzing property vibe...", // 3s
      "🔒 Verifying trust signals...", // 4.5s
      "✨ Finalizing listing...", // 6s
    ];
    let i = 0;
    setProgressMsg(messages[0]);

    return setInterval(() => {
      i++;
      if (i < messages.length) setProgressMsg(messages[i]);
    }, 1500);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("uploading");
    const timer = startProgressSimulation();

    const formData = new FormData();
    formData.append("price", price);
    formData.append("currency", "GHS");
    formData.append("location_hint", hint);
    // Append all files
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      const res = await fetch(
        "https://asta-insights.onrender.com/listings/create",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await res.json();
      clearInterval(timer);

      if (data.status === "success") {
        setStatus("success");
        // Redirect to the new listing page or show success modal
        console.log("AI Insights:", data.insights);
        alert(
          `Listing Created in ${data.location}! Score: ${data.insights.score}/10`
        );
      } else {
        setStatus("error");
        alert("Upload Failed: " + (data.detail || data.message));
      }
    } catch (err) {
      clearInterval(timer);
      setStatus("error");
      console.error(err);
    }
  };

  return (
    <div className="p-6 max-w-md mx-auto bg-white rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">⚡ Lazy Agent Upload</h2>

      {status === "idle" ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Photos
            </label>
            <input
              type="file"
              multiple
              accept="image/*,.heic"
              onChange={(e) => setFiles(e.target.files)}
              className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Price (GHS)
            </label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
              placeholder="e.g. 150000"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Location Hint (Optional)
            </label>
            <input
              type="text"
              value={hint}
              onChange={(e) => setHint(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
              placeholder="e.g. GA-182-9988 or New Ningo"
            />
            <p className="text-xs text-gray-500 mt-1">
              Leave blank if photos have GPS.
            </p>
          </div>

          <button
            type="submit"
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none"
          >
            🚀 Publish Listing
          </button>
        </form>
      ) : (
        <div className="text-center py-10">
          {status === "uploading" && (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-lg font-medium text-gray-900 animate-pulse">
                {progressMsg}
              </p>
            </>
          )}
          {status === "success" && (
            <div className="text-green-600">
              <span className="text-4xl">✅</span>
              <p className="text-lg font-bold mt-2">Success!</p>
              <p>Redirecting...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
