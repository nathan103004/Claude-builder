'use client';

import { useState, useRef, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { RvsqServiceType } from './ServiceTypeSelector';

export interface ChatPanelProps {
  locale: string;
  onServiceTypeSelect: (type: RvsqServiceType) => void;
  onEmergencySelect: () => void;
}

type Message = { role: 'user' | 'assistant'; content: string };

export default function ChatPanel({ locale, onServiceTypeSelect, onEmergencySelect }: ChatPanelProps) {
  const t = useTranslations('chatbot');

  const [isOpen, setIsOpen] = useState(false);
  const [available, setAvailable] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamBuffer, setStreamBuffer] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const triggerButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamBuffer]);

  // Focus management: move focus into/out of panel on open/close
  useEffect(() => {
    if (isOpen) {
      textareaRef.current?.focus();
    } else {
      triggerButtonRef.current?.focus();
    }
  }, [isOpen]);

  // Focus trap: keep keyboard navigation within the panel when open
  useEffect(() => {
    if (!isOpen) return;
    const panel = panelRef.current;
    if (!panel) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key !== 'Tab') return;
      const focusable = Array.from(
        panel!.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])'
        )
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const userMessageCount = messages.filter((m) => m.role === 'user').length;
  const inputDisabled = streaming || userMessageCount >= 3;

  async function handleSend() {
    if (!input.trim() || streaming) return;
    const userMsg: Message = { role: 'user', content: input.trim() };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput('');
    setStreaming(true);
    setStreamBuffer('');

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: nextMessages, locale }),
      });

      if (resp.status === 503) {
        setAvailable(false);
        setIsOpen(false);
        return;
      }

      const reader = resp.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let assistantContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        let eventType = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const raw = line.slice(6);
            if (eventType === 'token') {
              const { text } = JSON.parse(raw);
              assistantContent += text;
              setStreamBuffer(assistantContent);
            } else if (eventType === 'result') {
              const result = JSON.parse(raw);
              setMessages((prev) => [...prev, { role: 'assistant', content: assistantContent }]);
              setStreamBuffer('');
              setStreaming(false);
              if (result.service_type === 'emergency') {
                setIsOpen(false);
                onEmergencySelect();
              } else {
                onServiceTypeSelect(result.service_type as RvsqServiceType);
                setIsOpen(false);
              }
              return;
            }
            eventType = '';
          }
        }
      }

      // Stream ended without result event — save assistant message for next turn
      if (assistantContent) {
        setMessages((prev) => [...prev, { role: 'assistant', content: assistantContent }]);
      }
      setStreamBuffer('');
    } catch {
      // ignore errors silently — user can retry
    } finally {
      setStreaming(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  if (!available) return null;

  return (
    <>
      {/* Floating trigger button */}
      {!isOpen && (
        <button
          ref={triggerButtonRef}
          type="button"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 bg-blue-600 text-white rounded-full px-4 py-3 shadow-lg hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-300"
        >
          {t('trigger')}
        </button>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-40"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Slide-up panel */}
      <div
        ref={panelRef}
        role="dialog"
        aria-labelledby="chat-heading"
        aria-modal="true"
        className={[
          'fixed bottom-0 left-0 right-0 md:left-auto md:right-6 md:bottom-6 md:w-96',
          'bg-white rounded-t-2xl md:rounded-2xl shadow-2xl flex flex-col z-50 max-h-[80vh]',
          'transition-transform duration-300',
          isOpen ? 'translate-y-0' : 'translate-y-full',
        ].join(' ')}
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <span id="chat-heading" className="font-semibold">{t('heading')}</span>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="text-gray-500 hover:text-gray-700 text-sm focus:outline-none"
          >
            {t('close')}
          </button>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={
                msg.role === 'user'
                  ? 'self-end bg-blue-600 text-white rounded-2xl rounded-br-sm px-3 py-2 text-sm max-w-[80%]'
                  : 'self-start bg-gray-100 text-gray-800 rounded-2xl rounded-bl-sm px-3 py-2 text-sm max-w-[80%]'
              }
            >
              {msg.content}
            </div>
          ))}

          {/* Streaming state — live region announces to screen readers */}
          <div aria-live="polite" aria-atomic="true">
            {streaming && streamBuffer === '' && (
              <div className="self-start bg-gray-100 text-gray-800 rounded-2xl rounded-bl-sm px-3 py-2 text-sm max-w-[80%]">
                {t('thinking')}
              </div>
            )}
            {streaming && streamBuffer !== '' && (
              <div className="self-start bg-gray-100 text-gray-800 rounded-2xl rounded-bl-sm px-3 py-2 text-sm max-w-[80%]">
                {streamBuffer}
                <span className="inline-block w-1 h-3 ml-0.5 bg-gray-600 animate-pulse" />
              </div>
            )}
          </div>

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="border-t p-3 flex gap-2">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('placeholder')}
            aria-label={t('placeholder')}
            disabled={inputDisabled}
            className="flex-1 border rounded-lg px-3 py-2 text-sm resize-none disabled:opacity-50"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={inputDisabled}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t('send')}
          </button>
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-gray-400 text-center px-4 pb-2">{t('disclaimer')}</p>
      </div>
    </>
  );
}
