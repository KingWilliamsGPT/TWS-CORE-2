"use client";

import React, { useState } from 'react';
import { AlertCircle, CheckCircle, XCircle, Loader2, Send, Trash2, Copy } from 'lucide-react';

const OAuthTestApp = () => {
    const [apiUrl, setApiUrl] = useState('http://localhost:9000/api/social');
    const [provider, setProvider] = useState('google-oauth2');
    const [accessToken, setAccessToken] = useState('');
    const [testResults, setTestResults] = useState([]);
    const [loading, setLoading] = useState(false);

    const providers = [
        { value: 'google-oauth2', label: 'Google OAuth2' },
        { value: 'facebook', label: 'Facebook' },
        { value: 'twitter', label: 'Twitter' },
        { value: 'github', label: 'GitHub' }
    ];

    const testCases = [
        {
            name: 'Valid Token',
            description: 'Test with a valid OAuth token',
            token: 'valid_token_12345',
            expectSuccess: true
        },
        {
            name: 'Invalid Token',
            description: 'Test with an invalid token',
            token: 'invalid_token',
            expectSuccess: false
        },
        {
            name: 'Empty Token',
            description: 'Test with empty token',
            token: '',
            expectSuccess: false
        },
        {
            name: 'Malformed Token',
            description: 'Test with malformed token',
            token: 'abc123!@#',
            expectSuccess: false
        }
    ];

    const makeRequest = async (token) => {
        const endpoint = `${apiUrl}/${provider}/`;
        const startTime = Date.now();

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ access_token: token })
            });

            const duration = Date.now() - startTime;
            const data = await response.json();

            return {
                success: response.ok,
                status: response.status,
                data,
                duration,
                endpoint
            };
        } catch (error) {
            return {
                success: false,
                status: 0,
                data: { error: error.message },
                duration: Date.now() - startTime,
                endpoint,
                error: true
            };
        }
    };

    const runSingleTest = async (token = accessToken) => {
        setLoading(true);
        const result = await makeRequest(token);

        const testResult = {
            id: Date.now(),
            timestamp: new Date().toLocaleTimeString(),
            provider,
            token: token.substring(0, 20) + '...',
            ...result
        };

        setTestResults(prev => [testResult, ...prev]);
        setLoading(false);
        return result;
    };

    const runAllTests = async () => {
        setLoading(true);
        for (const testCase of testCases) {
            const result = await makeRequest(testCase.token);

            const testResult = {
                id: Date.now() + Math.random(),
                timestamp: new Date().toLocaleTimeString(),
                provider,
                testName: testCase.name,
                description: testCase.description,
                token: testCase.token || '(empty)',
                expectedSuccess: testCase.expectSuccess,
                ...result
            };

            setTestResults(prev => [testResult, ...prev]);
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        setLoading(false);
    };

    const clearResults = () => {
        setTestResults([]);
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
    };

    const getStatusColor = (result) => {
        if (result.error) return 'bg-red-100 border-red-300';
        if (result.success) return 'bg-green-100 border-green-300';
        return 'bg-yellow-100 border-yellow-300';
    };

    const getStatusIcon = (result) => {
        if (result.error) return <XCircle className="text-red-600" />;
        if (result.success) return <CheckCircle className="text-green-600" />;
        return <AlertCircle className="text-yellow-600" />;
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
            <div className="max-w-6xl mx-auto">
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                        OAuth Testing Dashboard
                    </h1>
                    <p className="text-gray-600">
                        Test your Django OAuth2 social authentication endpoints
                    </p>
                </div>

                {/* Configuration Panel */}
                <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">Configuration</h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                API Base URL
                            </label>
                            <input
                                type="text"
                                value={apiUrl}
                                onChange={(e) => setApiUrl(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="http://localhost:9000/api/social"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                OAuth Provider
                            </label>
                            <select
                                value={provider}
                                onChange={(e) => setProvider(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                                {providers.map(p => (
                                    <option key={p.value} value={p.value}>{p.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Access Token
                        </label>
                        <input
                            type="text"
                            value={accessToken}
                            onChange={(e) => setAccessToken(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Enter OAuth access token..."
                        />
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={() => runSingleTest()}
                            disabled={loading || !accessToken}
                            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                            {loading ? (
                                <Loader2 className="animate-spin" size={20} />
                            ) : (
                                <Send size={20} />
                            )}
                            Test Single Request
                        </button>

                        <button
                            onClick={runAllTests}
                            disabled={loading}
                            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                            {loading ? (
                                <Loader2 className="animate-spin" size={20} />
                            ) : (
                                <Send size={20} />
                            )}
                            Run All Test Cases
                        </button>

                        <button
                            onClick={clearResults}
                            disabled={testResults.length === 0}
                            className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors ml-auto"
                        >
                            <Trash2 size={20} />
                            Clear Results
                        </button>
                    </div>
                </div>

                {/* Test Cases Reference */}
                <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">Predefined Test Cases</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {testCases.map((test, idx) => (
                            <div key={idx} className="border border-gray-200 rounded-lg p-4">
                                <h3 className="font-semibold text-gray-900">{test.name}</h3>
                                <p className="text-sm text-gray-600 mb-2">{test.description}</p>
                                <div className="flex items-center justify-between">
                                    <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                                        {test.token || '(empty)'}
                                    </code>
                                    <span className={`text-xs px-2 py-1 rounded ${test.expectSuccess ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                        {test.expectSuccess ? 'Should Pass' : 'Should Fail'}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Results Panel */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">
                        Test Results ({testResults.length})
                    </h2>

                    {testResults.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            No test results yet. Run a test to see results here.
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {testResults.map((result) => (
                                <div
                                    key={result.id}
                                    className={`border-2 rounded-lg p-4 ${getStatusColor(result)}`}
                                >
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="flex items-center gap-3">
                                            {getStatusIcon(result)}
                                            <div>
                                                <h3 className="font-semibold text-gray-900">
                                                    {result.testName || 'Manual Test'}
                                                </h3>
                                                <p className="text-sm text-gray-600">
                                                    {result.timestamp} • {result.provider}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${result.success
                                                ? 'bg-green-600 text-white'
                                                : 'bg-red-600 text-white'
                                                }`}>
                                                {result.status || 'ERROR'}
                                            </span>
                                            <span className="text-sm text-gray-600">
                                                {result.duration}ms
                                            </span>
                                        </div>
                                    </div>

                                    {result.description && (
                                        <p className="text-sm text-gray-700 mb-2">{result.description}</p>
                                    )}

                                    {result.expectedSuccess !== undefined && (
                                        <div className="mb-2">
                                            <span className={`text-sm font-medium ${result.success === result.expectedSuccess
                                                ? 'text-green-700'
                                                : 'text-red-700'
                                                }`}>
                                                {result.success === result.expectedSuccess
                                                    ? '✓ Test passed as expected'
                                                    : '✗ Test failed unexpectedly'}
                                            </span>
                                        </div>
                                    )}

                                    <div className="mb-2">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-sm font-medium text-gray-700">Endpoint:</span>
                                            <button
                                                onClick={() => copyToClipboard(result.endpoint)}
                                                className="text-blue-600 hover:text-blue-800"
                                            >
                                                <Copy size={14} />
                                            </button>
                                        </div>
                                        <code className="block text-xs bg-white/50 px-2 py-1 rounded">
                                            {result.endpoint}
                                        </code>
                                    </div>

                                    <div className="mb-2">
                                        <span className="text-sm font-medium text-gray-700">Token:</span>
                                        <code className="block text-xs bg-white/50 px-2 py-1 rounded mt-1">
                                            {result.token}
                                        </code>
                                    </div>

                                    <details className="mt-3">
                                        <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                                            Response Data
                                        </summary>
                                        <pre className="mt-2 text-xs bg-white/50 p-3 rounded overflow-x-auto">
                                            {JSON.stringify(result.data, null, 2)}
                                        </pre>
                                    </details>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Documentation */}
                <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">How to Use</h2>
                    <div className="space-y-3 text-sm text-gray-700">
                        <p><strong>1. Configure your API:</strong> Set the base URL to your Django backend (e.g., http://localhost:9000/api/social)</p>
                        <p><strong>2. Select Provider:</strong> Choose the OAuth provider you want to test</p>
                        <p><strong>3. Get Access Token:</strong> Obtain a real OAuth token from the provider's OAuth playground or developer console</p>
                        <p><strong>4. Test:</strong> Use "Test Single Request" for manual testing or "Run All Test Cases" for automated testing</p>
                        <p className="text-blue-600"><strong>Tip:</strong> Check the browser console for any CORS errors if requests fail</p>
                    </div>

                    <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <h3 className="font-semibold text-yellow-900 mb-2">⚠️ CORS Setup Required</h3>
                        <p className="text-sm text-yellow-800">
                            Make sure your Django backend has CORS configured:
                        </p>
                        <pre className="mt-2 text-xs bg-yellow-100 p-2 rounded overflow-x-auto">
                            pip install django-cors-headers
                            # Add to INSTALLED_APPS: 'corsheaders'
                            # Add to MIDDLEWARE: 'corsheaders.middleware.CorsMiddleware'
                            # Add: CORS_ALLOW_ALL_ORIGINS = True  # For testing only!
                        </pre>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default OAuthTestApp;