import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  IconButton,
  useTheme
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import EmailIcon from '@mui/icons-material/Email';
import { styled } from '@mui/material/styles';

const MessageContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  padding: '16px',
  marginBottom: '8px',
  borderRadius: '8px',
  maxWidth: '80%',
  wordBreak: 'break-word',
}));

const UserMessage = styled(MessageContainer)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  color: 'white',
  marginLeft: 'auto',
}));

const AgentMessage = styled(MessageContainer)(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  color: theme.palette.text.primary,
  marginRight: 'auto',
  border: `1px solid ${theme.palette.divider}`,
}));

const ChatInterface = ({ onContinue, onSendEmail, onMessageSent }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const theme = useTheme();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      isUser: true,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    onMessageSent(userMessage);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Chat Messages */}
      <Box 
        sx={{ 
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          backgroundColor: theme.palette.background.default,
          border: '1px solid',
          borderColor: theme.palette.divider
        }}
      >
        {messages.map((message, index) => (
          <Box key={message.id} sx={{ mb: 2 }}>
            {message.isUser ? (
              <UserMessage>
                <Typography variant="body1">{message.text}</Typography>
              </UserMessage>
            ) : (
              <AgentMessage>
                <Typography variant="body1">{message.text}</Typography>
              </AgentMessage>
            )}
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box 
        sx={{ 
          p: 2,
          borderTop: '1px solid',
          borderColor: theme.palette.divider,
          display: 'flex',
          gap: 1,
          alignItems: 'center'
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          InputProps={{
            endAdornment: (
              <IconButton 
                color="primary" 
                onClick={handleSendMessage}
                disabled={isLoading || !inputValue.trim()}
              >
                <SendIcon />
              </IconButton>
            ),
          }}
        />

        <Button
          variant="contained"
          color="primary"
          onClick={onContinue}
          disabled={isLoading}
          sx={{ ml: 1 }}
        >
          Continue
        </Button>

        <Button
          variant="contained"
          color="secondary"
          onClick={onSendEmail}
          disabled={isLoading}
          startIcon={<EmailIcon />}
          sx={{ ml: 1 }}
        >
          Send Email
        </Button>
      </Box>
    </Box>
  );
};

export default ChatInterface;
