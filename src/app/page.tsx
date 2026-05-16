// @ts-nocheck
'use client';

import { useState, useRef, useEffect } from 'react';
import { Mic, Square, Play, RefreshCcw, Bot, User, ChevronRight, Star, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function AITrenajyor() {
  const [scenarios, setScenarios] = useState({});
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [step, setStep] = useState('selection'); // selection, training, evaluation
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [evaluation, setEvaluation] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const messagesEndRef = useRef(null);
  const audioQueue = useRef([]);
  const isPlayingAudio = useRef(false);

  useEffect(() => {
    fetch('http://localhost:8000/scenarios')
      .then(res => res.json())
      .then(data => setScenarios(data));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startScenario = async (id) => {
    setSelectedScenario(id);
    setIsProcessing(true);
    
    try {
      const formData = new FormData();
      formData.append('scenario_id', id);
      
      const res = await fetch('http://localhost:8000/start', {
        method: 'POST',
        body: formData,
      });
      
      const data = await res.json();
      setMessages([{ role: 'assistant', content: data.llm_text }]);
      setStep('training');
      
      if (data.audio_base64) {
        queueAudio(data.audio_base64);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  const queueAudio = (base64) => {
    audioQueue.current.push(base64);
    processAudioQueue();
  };

  const processAudioQueue = () => {
    if (isPlayingAudio.current || audioQueue.current.length === 0) return;

    isPlayingAudio.current = true;
    const base64 = audioQueue.current.shift();
    const audio = new Audio(`data:audio/mp3;base64,${base64}`);
    
    audio.onended = () => {
      isPlayingAudio.current = false;
      processAudioQueue();
    };
    
    audio.play();
  };

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    audioChunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (e) => {
      audioChunksRef.current.push(e.data);
    };

    mediaRecorderRef.current.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
      processAudioStream(audioBlob);
    };

    mediaRecorderRef.current.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current.stop();
    setIsRecording(false);
  };

  const processAudioStream = async (blob) => {
    setIsProcessing(true);
    
    try {
      const formData = new FormData();
      formData.append('audio', blob);
      formData.append('scenario_id', selectedScenario);
      formData.append('history', JSON.stringify(messages));
      
      const response = await fetch('http://localhost:8000/process-stream', {
        method: 'POST',
        body: formData,
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      // Initialize assistant message if not already there
      let currentAssistantMessage = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep the last partial line

        for (const line of lines) {
          if (!line.trim()) continue;
          const data = JSON.parse(line);

          if (data.type === 'stt') {
            setMessages(prev => [...prev, { role: 'user', content: data.text }]);
            // Add a placeholder for assistant response
            setMessages(prev => [...prev, { role: 'assistant', content: '' }]);
          } else if (data.type === 'llm_chunk') {
            currentAssistantMessage += data.text;
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1].content = currentAssistantMessage;
              return newMessages;
            });
            
            if (data.audio_base64) {
              queueAudio(data.audio_base64);
            }
          } else if (data.type === 'done') {
            if (data.is_final) {
              setStep('evaluation');
            }
          }
        }
      }
    } catch (err) {
      console.error('Streaming error:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const reset = () => {
    setStep('selection');
    setSelectedScenario(null);
    setMessages([]);
    setEvaluation(null);
    audioQueue.current = [];
    isPlayingAudio.current = false;
  };

  if (step === 'selection') {
    return (
      <div className="min-h-screen bg-[#0d1117] text-white p-8">
        <div className="max-w-6xl mx-auto">
          <header className="mb-12 text-center">
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
              AI-Trenajyor
            </h1>
            <p className="text-gray-400 text-xl">Bank xodimlari uchun ovozli muloqot simulyatori</p>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {['Nedovolniy', 'Prodaja', 'Moshennik'].map(cat => (
              <div key={cat} className="space-y-4">
                <h2 className="text-2xl font-semibold border-b border-gray-800 pb-2 mb-6 flex items-center gap-2">
                  {cat === 'Nedovolniy' && <AlertCircle className="text-red-400" />}
                  {cat === 'Prodaja' && <Star className="text-yellow-400" />}
                  {cat === 'Moshennik' && <CheckCircle2 className="text-green-400" />}
                  {cat === 'Nedovolniy' ? 'Norozi Mijozlar' : cat === 'Prodaja' ? 'Mahsulot Sotish' : 'Firgarlik Xavfi'}
                </h2>
                <div className="space-y-3">
                  {Object.entries(scenarios)
                    .filter(([id, s]) => s.category === cat)
                    .map(([id, s]) => (
                      <button
                        key={id}
                        onClick={() => startScenario(id)}
                        className="w-full text-left p-4 rounded-xl bg-gray-900 border border-gray-800 hover:border-blue-500 hover:bg-gray-800 transition-all group"
                      >
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs font-mono text-blue-400">{id}</span>
                          <ChevronRight size={16} className="text-gray-600 group-hover:text-blue-400 transition-colors" />
                        </div>
                        <h3 className="font-medium text-gray-200">{s.title}</h3>
                        <p className="text-xs text-gray-500 line-clamp-1 mt-1">{s.description}</p>
                      </button>
                    ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0d1117] flex flex-col">
      {/* Header */}
      <header className="p-6 border-b border-gray-800 bg-[#0d1117]/80 backdrop-blur-md sticky top-0 z-10 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-900/20">
            <Bot size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">
              {scenarios[selectedScenario]?.title}
            </h1>
            <p className="text-xs text-gray-400">Virtual Mijoz bilan muloqot</p>
          </div>
        </div>
        <button onClick={reset} className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 transition-colors">
          <RefreshCcw size={20} />
        </button>
      </header>

      {/* Chat Messages */}
      <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-4xl mx-auto w-full">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${m.role === 'user' ? 'bg-blue-600' : 'bg-gray-800'}`}>
                {m.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={`p-4 rounded-2xl ${
                m.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-none' 
                  : 'bg-gray-800 text-gray-200 rounded-tl-none border border-gray-700'
              } shadow-sm`}>
                {m.content.split('\n').map((line, idx) => {
                  if (line.startsWith('###')) return <h3 key={idx} className="font-bold text-xl my-4 text-blue-400">{line.replace(/###/g, '').trim()}</h3>;
                  if (line.startsWith('* **')) return <p key={idx} className="ml-4 mb-2"><strong>{line.split('**')[1]}</strong>{line.split('**')[2]}</p>;
                  return <p key={idx} className={line.startsWith('#') ? 'font-bold text-lg mb-2' : 'mb-1'}>
                    {line}
                  </p>;
                })}
              </div>
            </div>
          </div>
        ))}
        {isProcessing && (
          <div className="flex justify-start">
             <div className="bg-gray-800 p-4 rounded-2xl rounded-tl-none animate-pulse flex gap-2">
                <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-75"></div>
                <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-150"></div>
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Controls */}
      <footer className="p-8 bg-gradient-to-t from-[#0d1117] to-transparent">
        {step === 'training' && (
          <div className="flex flex-col items-center gap-6">
            <div className={`relative ${isRecording ? 'scale-110' : 'scale-100'} transition-transform duration-300`}>
              {isRecording && (
                <div className="absolute inset-0 bg-red-500/20 rounded-full animate-ping"></div>
              )}
              <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing}
                className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
                  isRecording 
                    ? 'bg-red-500 hover:bg-red-600' 
                    : 'bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700'
                } shadow-xl`}
              >
                {isRecording ? <Square size={32} fill="white" /> : <Mic size={32} />}
              </button>
            </div>
            <p className={`text-sm font-medium ${isRecording ? 'text-red-400 animate-pulse' : 'text-gray-400'}`}>
              {isRecording ? "Sizni eshityapman..." : isProcessing ? "O'ylayapman..." : "Gapirish uchun tugmani bosing"}
            </p>
          </div>
        )}
        
        {step === 'evaluation' && (
          <div className="max-w-2xl mx-auto text-center space-y-6">
            <div className="bg-blue-600/10 border border-blue-500/30 p-6 rounded-2xl">
               <h2 className="text-2xl font-bold text-blue-400 mb-2">Simulyatsiya Yakunlandi!</h2>
               <p className="text-gray-400">AI-Auditordan baholash natijasini yuqorida ko'rishingiz mumkin.</p>
            </div>
            <button
              onClick={reset}
              className="px-8 py-4 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-semibold transition-all flex items-center gap-2 mx-auto"
            >
              <RefreshCcw size={20} />
              Boshidan boshlash
            </button>
          </div>
        )}
      </footer>
    </div>
  );
}
