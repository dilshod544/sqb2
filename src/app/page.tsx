// @ts-nocheck
'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, Square, RefreshCcw, Bot, User, ChevronRight, Star, AlertCircle, CheckCircle2 } from 'lucide-react';

const EMOTION_COLORS: Record<string, { bg: string; emoji: string; label: string }> = {
  "g'azab":   { bg: '#fee2e2', emoji: '😡', label: "G'azablangan" },
  "yig'i":    { bg: '#e0f2fe', emoji: '😢', label: "Yig'layapti" },
  "vahima":   { bg: '#fef9c3', emoji: '😰', label: 'Vahimada' },
  "xotirjam": { bg: '#dcfce7', emoji: '😌', label: 'Tinch' },
  "quvonch":  { bg: '#dcfce7', emoji: '😊', label: 'Xursand' },
  "kinoya":   { bg: '#f3e8ff', emoji: '😒', label: 'Kinoyali' },
  "hayrat":   { bg: '#fff7ed', emoji: '😲', label: 'Hayron' },
  "kulgi":    { bg: '#fef3c7', emoji: '😄', label: 'Kulmoqda' },
};

function parseMessageEmotion(text: string) {
  const emotionMatch = text.match(/\[(g'azab|yig'i|vahima|xotirjam|quvonch|kinoya|hayrat|kulgi)\]/);
  const emotion = emotionMatch ? emotionMatch[1] : null;
  const cleanText = text.replace(/\[.*?\]/g, '').trim();
  return { emotion, cleanText };
}

function parseScore(text: string, pattern: RegExp) {
  const m = text.match(pattern);
  return m ? m[1] : null;
}

function EvaluationPanel({ text }: { text: string }) {
  const total = parseScore(text, /UMUMIY BALL:\s*(\d+)/i);
  const emp = parseScore(text, /Mijozga munosabat[^:]*:\s*(\d+)/i);
  const stress = parseScore(text, /Bosimga chidash[^:]*:\s*(\d+)/i);
  const solve = parseScore(text, /Muammoni hal qilish[^:]*:\s*(\d+)/i);
  const scoreNum = total ? parseInt(total, 10) : 0;
  const grade =
    scoreNum >= 25 ? { label: 'A\'lo!', color: 'text-green-400', bg: 'bg-green-500/20' } :
    scoreNum >= 18 ? { label: 'Yaxshi', color: 'text-blue-400', bg: 'bg-blue-500/20' } :
    scoreNum >= 10 ? { label: 'O\'rta', color: 'text-yellow-400', bg: 'bg-yellow-500/20' } :
    { label: 'Yaxshilash kerak', color: 'text-red-400', bg: 'bg-red-500/20' };

  return (
    <div className="space-y-6">
      <div className={`text-center p-6 rounded-2xl border border-gray-700 ${grade.bg}`}>
        <p className="text-sm text-gray-400 mb-1">Umumiy natija</p>
        <p className={`text-5xl font-bold ${grade.color}`}>{total ?? '—'}/30</p>
        <p className={`text-xl font-semibold mt-2 ${grade.color}`}>{grade.label}</p>
        <div className="flex justify-center gap-6 mt-4 text-sm text-gray-300">
          <span>Munosabat: {emp ?? '—'}/10</span>
          <span>Stress: {stress ?? '—'}/10</span>
          <span>Hal qilish: {solve ?? '—'}/10</span>
        </div>
      </div>
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 text-gray-200 text-sm whitespace-pre-wrap leading-relaxed max-h-[50vh] overflow-y-auto">
        {text}
      </div>
    </div>
  );
}

function MessageBubble({ role, content, isEvaluation }: { role: string; content: string; isEvaluation?: boolean }) {
  if (isEvaluation) {
    return (
      <div className="w-full max-w-none">
        <EvaluationPanel text={content} />
      </div>
    );
  }

  const { emotion, cleanText } = parseMessageEmotion(content);
  const emotionStyle = emotion ? EMOTION_COLORS[emotion] : null;
  const displayText = cleanText || content;

  return (
    <div className={`max-w-[80%] flex gap-3 ${role === 'user' ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${role === 'user' ? 'bg-blue-600' : 'bg-gray-800'}`}>
        {role === 'user' ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div
        className={`p-4 rounded-2xl ${
          role === 'user'
            ? 'bg-blue-600 text-white rounded-tr-none'
            : 'bg-gray-800 text-gray-200 rounded-tl-none border border-gray-700'
        } shadow-sm`}
        style={emotionStyle && role === 'assistant' ? { backgroundColor: emotionStyle.bg, color: '#1f2937' } : undefined}
      >
        {emotionStyle && role === 'assistant' && (
          <div className="flex items-center gap-2 mb-2 text-sm font-medium">
            <span>{emotionStyle.emoji}</span>
            <span>{emotionStyle.label}</span>
          </div>
        )}
        <p className="leading-relaxed">{displayText}</p>
      </div>
    </div>
  );
}

export default function AITrenajyor() {
  const [scenarios, setScenarios] = useState({});
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [step, setStep] = useState('selection');
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [evaluationText, setEvaluationText] = useState('');
  const [turnCount, setTurnCount] = useState(0);
  const [lastHeard, setLastHeard] = useState('');

  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const messagesEndRef = useRef(null);
  const audioQueue = useRef([]);
  const isPlayingAudio = useRef(false);
  const isRecordingRef = useRef(false);

  useEffect(() => {
    fetch('http://localhost:8000/scenarios')
      .then(res => res.json())
      .then(data => setScenarios(data))
      .catch(() => setErrorMsg('Backend ulanmadi. Terminal 2 da: python3 -m backend.main'));

    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => {
        if (data.ollama && !data.ollama.ready) {
          setErrorMsg(
            `Ollama model topilmadi (${data.ollama.configured}). Terminalda: ollama pull qwen2.5:7b-instruct`
          );
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, evaluationText]);

  const stopMediaTracks = useCallback(() => {
    mediaStreamRef.current?.getTracks().forEach(t => t.stop());
    mediaStreamRef.current = null;
  }, []);

  const startScenario = async (id) => {
    setSelectedScenario(id);
    setIsProcessing(true);
    setErrorMsg(null);
    setEvaluationText('');
    setTurnCount(0);

    try {
      const formData = new FormData();
      formData.append('scenario_id', id);
      const res = await fetch('http://localhost:8000/start', { method: 'POST', body: formData });
      const data = await res.json();
      setMessages([{ role: 'assistant', content: data.llm_text }]);
      setStep('training');
      if (data.audio_base64) queueAudio(data.audio_base64);
    } catch (err) {
      setErrorMsg('Serverga ulanib bo\'lmadi');
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
    audio.onerror = () => {
      isPlayingAudio.current = false;
      processAudioQueue();
    };
    audio.play().catch(() => {
      isPlayingAudio.current = false;
      processAudioQueue();
    });
  };

  const startRecording = async () => {
    if (isProcessing || isRecordingRef.current) return;
    setErrorMsg(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      audioChunksRef.current = [];

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        isRecordingRef.current = false;
        setIsRecording(false);
        stopMediaTracks();
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        if (blob.size > 500) {
          processAudioStream(blob);
        } else {
          setErrorMsg('Juda qisqa yozildi. Qayta gapiring.');
        }
      };

      recorder.start(200);
      isRecordingRef.current = true;
      setIsRecording(true);
    } catch (err) {
      setErrorMsg('Mikrofon ruxsati kerak. Brauzer sozlamalaridan yoqing.');
      console.error(err);
    }
  };

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state === 'recording') {
      recorder.stop();
    }
  }, []);

  const processAudioStream = async (blob) => {
    setIsProcessing(true);
    setErrorMsg(null);

    try {
      const formData = new FormData();
      formData.append('audio', blob, 'recording.webm');
      formData.append('scenario_id', selectedScenario);
      formData.append('history', JSON.stringify(messages));

      const response = await fetch('http://localhost:8000/process-stream', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Server xato');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentAssistantMessage = '';
      let inEvaluation = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          const data = JSON.parse(line);

          if (data.type === 'error') {
            setErrorMsg(data.text);
            continue;
          } else if (data.type === 'stt') {
            setLastHeard(data.text);
            setTurnCount(c => c + 1);
            setMessages(prev => [
              ...prev,
              { role: 'user', content: data.text },
              { role: 'assistant', content: '', isEvaluation: false },
            ]);
          } else if (data.type === 'llm_chunk') {
            if (data.is_evaluation) {
              inEvaluation = true;
              currentAssistantMessage += data.text;
              setEvaluationText(currentAssistantMessage);
              setMessages(prev => {
                const copy = [...prev];
                const last = copy[copy.length - 1];
                if (last?.role === 'assistant') {
                  copy[copy.length - 1] = { role: 'assistant', content: currentAssistantMessage, isEvaluation: true };
                } else {
                  copy.push({ role: 'assistant', content: currentAssistantMessage, isEvaluation: true });
                }
                return copy;
              });
            } else {
              currentAssistantMessage += (currentAssistantMessage ? ' ' : '') + data.text;
              setMessages(prev => {
                const copy = [...prev];
                copy[copy.length - 1] = { role: 'assistant', content: currentAssistantMessage, isEvaluation: false };
                return copy;
              });
              if (data.audio_base64) queueAudio(data.audio_base64);
            }
          } else if (data.type === 'done') {
            if (data.is_final) {
              if (data.evaluation) setEvaluationText(data.evaluation);
              setStep('evaluation');
            }
          }
        }
      }
    } catch (err) {
      setErrorMsg('Xatolik yuz berdi. Backend va Ollama ishlayotganini tekshiring.');
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  const reset = () => {
    stopMediaTracks();
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setStep('selection');
    setSelectedScenario(null);
    setMessages([]);
    setEvaluationText('');
    setErrorMsg(null);
    setTurnCount(0);
    audioQueue.current = [];
    isPlayingAudio.current = false;
    isRecordingRef.current = false;
    setIsRecording(false);
  };

  if (step === 'selection') {
    return (
      <div className="min-h-screen bg-[#0d1117] text-white p-8">
        <div className="max-w-6xl mx-auto">
          <header className="mb-12 text-center">
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
              AI-Trenajyor
            </h1>
            <p className="text-gray-400 text-xl">Yangi bank xodimlari uchun mijoz bilan muloqot mashqi</p>
            <p className="text-gray-500 text-sm mt-2">O&apos;zbekcha gapiring · mikrofon → STOP → mijoz javob beradi</p>
          </header>
          {errorMsg && (
            <p className="text-center text-red-400 mb-6 bg-red-500/10 p-3 rounded-lg">{errorMsg}</p>
          )}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {['Nedovolniy', 'Prodaja', 'Moshennik'].map(cat => (
              <div key={cat} className="space-y-4">
                <h2 className="text-2xl font-semibold border-b border-gray-800 pb-2 mb-6 flex items-center gap-2">
                  {cat === 'Nedovolniy' && <AlertCircle className="text-red-400" />}
                  {cat === 'Prodaja' && <Star className="text-yellow-400" />}
                  {cat === 'Moshennik' && <CheckCircle2 className="text-green-400" />}
                  {cat === 'Nedovolniy' ? 'Norozi Mijozlar' : cat === 'Prodaja' ? 'Mahsulot Sotish' : 'Firibgarlik Xavfi'}
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
                          <ChevronRight size={16} className="text-gray-600 group-hover:text-blue-400" />
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
      <header className="p-6 border-b border-gray-800 bg-[#0d1117]/80 backdrop-blur-md sticky top-0 z-10 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-400 flex items-center justify-center">
            <Bot size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">{scenarios[selectedScenario]?.title}</h1>
            <p className="text-xs text-gray-400">
              {step === 'evaluation' ? 'Baholash natijasi' : `Muloqot bosqichi · ${turnCount} ta javob`}
            </p>
          </div>
        </div>
        <button onClick={reset} type="button" className="p-2 hover:bg-gray-800 rounded-lg text-gray-400">
          <RefreshCcw size={20} />
        </button>
      </header>

      <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-4xl mx-auto w-full">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.isEvaluation ? 'justify-center w-full' : m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <MessageBubble role={m.role} content={m.content} isEvaluation={m.isEvaluation} />
          </div>
        ))}
        {isProcessing && !isRecording && (
          <div className="flex justify-start">
            <div className="bg-gray-800 p-4 rounded-2xl rounded-tl-none animate-pulse flex gap-2 items-center">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '75ms' }} />
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="text-gray-400 text-sm ml-2">Mijoz o&apos;ylayapti...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <footer className="p-8 bg-gradient-to-t from-[#0d1117] to-transparent">
        {errorMsg && (
          <p className="text-center text-red-400 text-sm mb-4 bg-red-500/10 py-2 px-4 rounded-lg max-w-md mx-auto">
            {errorMsg}
          </p>
        )}

        {lastHeard && step === 'training' && !errorMsg && (
          <p className="text-center text-gray-500 text-xs mb-3 max-w-md mx-auto">
            Sizning gapingiz eshitildi: <span className="text-blue-300">&quot;{lastHeard}&quot;</span>
          </p>
        )}

        {step === 'training' && (
          <div className="flex flex-col items-center gap-4">
            <div className="relative">
              {isRecording && (
                <div className="absolute inset-0 bg-red-500/20 rounded-full animate-ping pointer-events-none" />
              )}
              <button
                type="button"
                onPointerDown={(e) => {
                  e.preventDefault();
                  if (isRecordingRef.current) stopRecording();
                  else if (!isProcessing) startRecording();
                }}
                disabled={isProcessing && !isRecording}
                className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center transition-all ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 ring-4 ring-red-500/50'
                    : 'bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700'
                } shadow-xl`}
              >
                {isRecording ? <Square size={32} fill="white" /> : <Mic size={32} />}
              </button>
            </div>
            <p className={`text-sm font-medium ${isRecording ? 'text-red-400 animate-pulse' : 'text-gray-400'}`}>
              {isRecording
                ? '⏹ QIZIL tugmani bosing — yozish to\'xtaydi'
                : isProcessing
                  ? 'Mijoz javob bermoqda, kuting...'
                  : '🎤 O\'zbekcha gapiring — aniq, qisqa. Keyin qizil STOP'}
            </p>
          </div>
        )}

        {step === 'evaluation' && (
          <div className="max-w-2xl mx-auto text-center space-y-4">
            {evaluationText && <EvaluationPanel text={evaluationText} />}
            <button
              type="button"
              onClick={reset}
              className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold flex items-center gap-2 mx-auto"
            >
              <RefreshCcw size={20} />
              Yangi ssenariy
            </button>
          </div>
        )}
      </footer>
    </div>
  );
}
