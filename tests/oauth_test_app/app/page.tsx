"use client";

import React, { useState } from "react";
import { GoogleOAuthProvider, GoogleLogin } from "@react-oauth/google";
import {
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Shield,
  Key,
  Mail,
  User,
  LogIn,
} from "lucide-react";

const GOOGLE_CLIENT_ID = "zeefas.apps.googleusercontent.com";

const OAuthTestApp = () => {
  const baseUrl = "http://localhost:9000/api/v1"; // Fixed: removed markdown formatting
  const [apiUrl, setApiUrl] = useState(`${baseUrl}/social`);
  const [authLogs, setAuthLogs] = useState<any[]>([]);
  const [jwtTokens, setJwtTokens] = useState<{
    access: string;
    refresh: string;
  } | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addLog = (type: string, message: string, data?: any) => {
    const log = {
      id: Date.now() + Math.random(),
      type,
      message,
      data,
      timestamp: new Date().toLocaleTimeString(),
    };
    setAuthLogs((prev) => [log, ...prev]);
  };

  const exchangeToken = async (credential: string) => {
    setLoading(true);
    const endpoint = `${apiUrl}/google-oauth2/`;
    addLog("info", `Sending Google credential to backend`, { endpoint });

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_token: credential }), // Fixed: send 'credential' instead of 'access_token'
      });
      const data = await res.json();

      if (res.ok) {
        // Fixed: Added null checks for data properties
        if (data.access && data.refresh) {
          setJwtTokens({ access: data.access, refresh: data.refresh });
          setCurrentUser(data.user || {});
          addLog("success", "Authentication successful!", data);
          setError(null);
        } else {
          addLog("error", "Invalid response format from backend", data);
          setError("Backend returned incomplete data");
        }
      } else {
        addLog("error", "Backend rejected Google token", data);
        setError(JSON.stringify(data));
      }
    } catch (err: any) {
      setError(err.message);
      addLog("error", "Network error", { error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = (credentialResponse: any) => {
    const token = credentialResponse.credential;
    console.log("credentials", credentialResponse);
    if (!token) {
      setError("No credential returned from Google");
      addLog("error", "No credential in response"); // Fixed: added log
      return;
    }
    addLog("success", "Received Google credential", {
      preview: token.substring(0, 20) + "...",
    });
    exchangeToken(token);
  };

  const handleGoogleError = () => {
    setError("Google login failed");
    addLog("error", "Google login failed");
  };

  const clearLogs = () => setAuthLogs([]);
  const handleLogout = () => {
    setCurrentUser(null);
    setJwtTokens(null);
    setError(null);
    addLog("info", "Logged out");
  };

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
        <div className="max-w-5xl mx-auto p-6">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-2">
              Real Google OAuth Test
            </h1>
            <p className="text-gray-600">Sign in using your Google account</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 space-y-6">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Django API Base URL
              </label>
              <input
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>

            {!currentUser ? (
              <div className="flex flex-col items-center space-y-4">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                />
                {loading && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Loader2 className="animate-spin" size={16} />
                    <span>Authenticating...</span>
                  </div>
                )}
                {error && (
                  <div className="text-red-600 text-sm flex items-center gap-2">
                    <XCircle size={16} />
                    {error}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-green-500 text-white rounded-full flex items-center justify-center">
                    {currentUser.picture ? (
                      <img
                        src={currentUser.picture}
                        alt="avatar"
                        className="w-full h-full rounded-full"
                      />
                    ) : (
                      <User size={24} />
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800">
                      {currentUser.name || "User"}
                    </h3>
                    <p className="text-sm text-gray-600 flex items-center gap-1">
                      <Mail size={14} /> {currentUser.email || "No email"}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 text-sm"
                >
                  Logout
                </button>
              </div>
            )}
          </div>

          <div className="mt-6 bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Shield className="text-indigo-600" size={20} />
                Logs
              </h2>
              <button
                onClick={clearLogs}
                className="text-xs px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
              >
                Clear
              </button>
            </div>
            <div className="max-h-[300px] overflow-y-auto text-xs space-y-2">
              {authLogs.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No logs yet.</p>
              ) : (
                authLogs.map((log) => (
                  <div
                    key={log.id}
                    className={`p-2 rounded border ${
                      log.type === "error"
                        ? "bg-red-50 border-red-200"
                        : log.type === "success"
                        ? "bg-green-50 border-green-200"
                        : "bg-blue-50 border-blue-200"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      {log.type === "success" && (
                        <CheckCircle className="text-green-600" size={14} />
                      )}
                      {log.type === "error" && (
                        <XCircle className="text-red-600" size={14} />
                      )}
                      {log.type === "info" && (
                        <AlertCircle className="text-blue-600" size={14} />
                      )}
                      <div>
                        <p className="font-medium text-gray-800">
                          {log.message}
                        </p>
                        {log.data && (
                          <details className="mt-1">
                            <summary className="cursor-pointer text-gray-600">
                              Details
                            </summary>
                            <pre className="bg-white/60 p-2 rounded mt-1 overflow-x-auto">
                              {JSON.stringify(log.data, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </GoogleOAuthProvider>
  );
};

export default OAuthTestApp;
