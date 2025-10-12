export default function ChatInterface({ onContinue, onSendEmail, onMessageSent }) {
  return (
    <div>
      <div>Chat Interface</div>
      <input placeholder="Type your message..." />
      <button onClick={() => onMessageSent('Test message')}>Send</button>
      <button onClick={onContinue}>Continue</button>
      <button onClick={onSendEmail}>Send Email</button>
    </div>
  );
}
