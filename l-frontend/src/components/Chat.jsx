import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  Button, TextField, Container, Box, Typography, Link, IconButton,
  Drawer, List, ListItem, ListItemText, Divider, AppBar, Toolbar,
  CssBaseline, createTheme, ThemeProvider, Chip, Tooltip, Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import { Menu as MenuIcon, Logout } from '@mui/icons-material';
import ChatMessage from './ChatMessage';


function generateSessionId() {
  return (
    Date.now().toString(36) +
    Math.random().toString(36).substring(2, 10)
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  // Use only generateSessionId for session ID
  const [currentSessionId, setCurrentSessionId] = useState(() => generateSessionId());
  const [showPopup, setShowPopup] = useState(false);
  // Remove consecutiveUserCount, add userMessageCount
  const [userMessageCount, setUserMessageCount] = useState(0);
  // Make threshold easy to change
  const POPUP_THRESHOLD = 5;
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);

  // Dynamic suggestion prompts that will update based on conversation stage
  const [suggestionPrompts, setSuggestionPrompts] = useState([
    "My car was stolen yesterday",
    "I need to know about starting a business in India",
    "I'm having an issue with my landlord",
    "What are my rights in a contract dispute?"
  ]);

  const theme = createTheme({
    palette: {
      mode: 'dark',
      background: {
        default: '#1A1A1A',
        paper: '#242424'
      },
      primary: {
        main: '#7C3AED',
        contrastText: '#ffffff'
      },
      secondary: {
        main: '#64748B'
      },
      text: {
        primary: '#F8FAFC',
        secondary: '#94A3B8'
      }
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            textTransform: 'none',
            fontWeight: 600,
          }
        }
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            input: {
              color: '#F8FAFC',
              backgroundColor: '#1E293B'
            }
          }
        }
      },
      MuiChip: {
        styleOverrides: {
          root: {
            transition: 'all 0.3s ease',
            borderRadius: 16,
            padding: '8px 12px',
            fontSize: '0.9rem',
            whiteSpace: 'normal',
            wordBreak: 'break-word',
            height: 'auto',
            minHeight: '32px',
            lineHeight: '1.4',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
            }
          }
        }
      }
    }
  });

  // Remove all axios calls to /api/chats
  // On mount, load chat history from sessionStorage
  useEffect(() => {
    const storedHistory = sessionStorage.getItem('chatHistory');
    if (storedHistory) {
      setHistory(JSON.parse(storedHistory));
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  // On every message send, update sessionStorage
  // Helper function to generate suggestion prompts based on conversation stage
  const generateStageSuggestions = (stage) => {
    const suggestions = {
      initial: [
        "My car was stolen yesterday",
        "I'm having an issue with my landlord",
        "I need help with a contract dispute",
        "Someone is threatening to sue me"
      ],
      details: [
        "What legal sections apply to my situation?",
        "Are there any relevant court cases?",
        "What are my legal options?",
        "What should I do next?"
      ],
      sections: [
        "Can you explain these sections in simpler terms?",
        "How do these laws apply to my case?",
        "Are there any relevant court cases?",
        "What's the practical impact of these laws?"
      ],
      cases: [
        "How do these cases affect my situation?",
        "What sections of law were applied in these cases?",
        "What was the final outcome in these cases?",
        "What are the implications for my case?"
      ],
      impact: [
        "What steps should I take next?",
        "What documentation do I need?",
        "Are there any deadlines I should be aware of?",
        "Should I consult a lawyer about this?"
      ],
      followup: [
        "Yes, I've filed an FIR",
        "No, I haven't reported it yet",
        "What sections of law apply to my case?",
        "What steps should I take next?"
      ]
    };
    
    return suggestions[stage] || suggestions.initial;
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    console.log('Sending message with session_id:', currentSessionId);
    const newMessages = [...messages, { type: 'user', content: input }];
    setMessages(newMessages);
    setLoading(true);
    // Count total user messages
    const newUserMessageCount = userMessageCount + 1;
    setUserMessageCount(newUserMessageCount);
    // Show popup on every POPUP_THRESHOLD-th user message
    if (newUserMessageCount % POPUP_THRESHOLD === 0) {
      setShowPopup(true);
    }
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/nyayadoot';
      // Use the correct API endpoint from the backend
      const aiResponse = await axios.post(
        `${API_URL}/query`,
        { query: input, session_id: currentSessionId }
      );
      
      // Handle the response which now includes references, cases, and conversation stage
      const botResponse = aiResponse.data.answer;
      const conversationStage = aiResponse.data.conversation_stage || "initial";
      
      // Update suggestion prompts based on conversation stage
      setSuggestionPrompts(generateStageSuggestions(conversationStage));
      
      const updatedMessages = [
        ...newMessages,
        { 
          type: 'bot', 
          content: botResponse,
          references: aiResponse.data.references || [],
          cases: aiResponse.data.cases || [],
          stage: conversationStage
        }
      ];
      
      setMessages(updatedMessages);
      // Save to sessionStorage as a new session
      const session = {
        session_id: currentSessionId,
        messages: updatedMessages,
        last_message_time: new Date().toISOString()
      };
      let updatedHistory = history.filter(s => s.session_id !== currentSessionId);
      updatedHistory = [session, ...updatedHistory];
      setHistory(updatedHistory);
      sessionStorage.setItem('chatHistory', JSON.stringify(updatedHistory));
    } catch (error) {
      console.error("API error:", error);
      setMessages(prev => [
        ...prev,
        { type: 'bot', content: 'Sorry, an error occurred. Please try again.' }
      ]);
    } finally {
      setInput('');
      setLoading(false);
    }
  };

  // When user starts a new chat, clear messages and update sessionStorage
  const startNewChat = async () => {
    const newSessionId = generateSessionId();
    console.log('Generated new session_id:', newSessionId);
    setMessages([]);
    setCurrentSessionId(newSessionId);
    setDrawerOpen(false);
    setUserMessageCount(0);
    
    // No need to call a reset endpoint since the backend uses the session_id
    // to track conversation state. A new session_id automatically starts a new conversation.
  };

  const toggleDrawer = (open) => () => {
    setDrawerOpen(open);
  };

  // When user clicks a history item, load messages from that session
  const handleHistoryClick = (session) => {
    setMessages(session.messages);
    setCurrentSessionId(session.session_id);
    setDrawerOpen(false);
  };

  const handleLogout = () => {
    navigate('/Nyayadoot/');
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {/* Popup Dialog for every 10th user message */}
      <Dialog open={showPopup} onClose={() => setShowPopup(false)}>
        <DialogTitle>For Better Assistance</DialogTitle>
        <DialogContent>
          <Typography>
            For better assistance, please visit{' '}
            <Link href="http://82.112.226.107/vaadvivaad/" target="_blank" rel="noopener noreferrer">
              <b>Click Here</b>
            </Link>.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPopup(false)} color="primary" variant="contained">
            Later
          </Button>
        </DialogActions>
      </Dialog>
      <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#1A1A1A' }}>
        <Drawer anchor="left" open={drawerOpen} onClose={toggleDrawer(false)}>
          <Box sx={{ width: 300, p: 2, bgcolor: '#1E293B', height: '100%' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ color: '#d4af37' }}>
              🗂️ Chat History
            </Typography>
            <Button fullWidth variant="contained" onClick={startNewChat} sx={{ mb: 2, bgcolor: '#d4af37', color: '#0a2463', fontWeight: 700, '&:hover': { bgcolor: '#c4a030' } }}>
              New Chat
            </Button>
            <Divider sx={{ mb: 2, bgcolor: '#d4af37' }} />
            <List>
              {history.length > 0 ? history.map((session, index) => (
                <ListItem
                  button
                  key={index}
                  onClick={() => handleHistoryClick(session)}
                  selected={session.session_id === currentSessionId}
                  sx={{ borderRadius: 2, mb: 1, bgcolor: session.session_id === currentSessionId ? '#d4af37' : 'inherit', color: session.session_id === currentSessionId ? '#0a2463' : 'inherit', fontWeight: session.session_id === currentSessionId ? 700 : 500 }}
                >
                  <ListItemText
                    primary={session.messages[0]?.message?.substring(0, 25) + "..."}
                    secondary={session.last_message_time ? new Date(session.last_message_time).toLocaleString() : 'No timestamp'}
                  />
                </ListItem>
              )) : (
                <Typography variant="body2" color="text.secondary">
                  No chats yet.
                </Typography>
              )}
            </List>
          </Box>
        </Drawer>
        <Container
          maxWidth={false}
          sx={{
            flexGrow: 1,
            display: 'flex',
            flexDirection: 'column',
            py: 4,
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            maxWidth: '1100px',
            margin: '0 auto',
          }}
        >
          <AppBar position="static" color="transparent" elevation={0} sx={{ mb: 2, maxWidth: '900px', mx: 'auto', width: '100%', bgcolor: 'transparent' }}>
            <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <IconButton edge="start" onClick={toggleDrawer(true)} sx={{ color: '#d4af37' }}>
                <MenuIcon />
              </IconButton>
              <Typography variant="h5" fontWeight="bold" sx={{ color: '#d4af37', letterSpacing: 1 }}>
                ⚖️ न्यायदूत
              </Typography>
              <IconButton onClick={handleLogout} sx={{ color: '#d4af37' }}>
                <Logout />
              </IconButton>
            </Toolbar>
          </AppBar>
          <Box
            sx={{
              flex: 1,
              p: 2,
              overflowY: 'auto',
              /* hide scrollbar but allow scroll */
              scrollbarWidth: 'none', /* Firefox */
              msOverflowStyle: 'none', /* IE 10+ */
              '&::-webkit-scrollbar': { width: 0, height: 0 }, /* WebKit */
              bgcolor: '#1E293B',
              borderRadius: 3,
              boxShadow: 3,
              position: 'relative',
              maxWidth: '900px',
              width: '100%',
              mx: 'auto',
              minHeight: '400px',
            }}
          >
            {messages.length === 0 && (
              <Box
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  p: 3,
                  bgcolor: '#232946',
                  borderRadius: 2,
                  boxShadow: 3,
                  maxWidth: '600px',
                  width: '100%',
                  textAlign: 'center',
                }}
              >
                <Typography
                  variant="subtitle1"
                  fontWeight="medium"
                  sx={{ color: '#d4af37', fontSize: '1.1rem', fontWeight: 700 }}
                  gutterBottom
                  align="center"
                >
                  Get Started with These Questions
                </Typography>
                <Divider sx={{ mb: 2, mt: 1, bgcolor: '#d4af37', height: 2, borderRadius: 1 }} />
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 1.2,
                    width: '100%',
                  }}
                >
                  {suggestionPrompts.map((prompt, index) => (
                    <Button
                      key={index}
                      variant="outlined"
                      onClick={() => setInput(prompt)}
                      sx={{
                        bgcolor: '#121212',
                        color: '#d4af37',
                        fontWeight: 500,
                        py: 1.1,
                        px: 2,
                        minWidth: '0',
                        maxWidth: '520px',
                        width: '100%',
                        fontSize: '0.98rem',
                        textAlign: 'center',
                        whiteSpace: 'normal',
                        wordBreak: 'break-word',
                        height: 'auto',
                        border: '1.5px solid',
                        borderColor: '#d4af37',
                        boxShadow: '0 1px 4px rgba(212, 175, 55, 0.08)',
                        borderRadius: '22px',
                        transition: 'all 0.3s cubic-bezier(.4,2,.6,1)',
                        mb: 0.5,
                        '&:hover': {
                          bgcolor: '#d4af37',
                          color: '#0a2463',
                          borderColor: '#c4a030',
                          transform: 'translateY(-2px) scale(1.03)',
                          boxShadow: '0 4px 12px rgba(212, 175, 55, 0.13)',
                        },
                        overflowWrap: 'break-word',
                        display: 'block',
                        margin: '0 auto',
                      }}
                    >
                      {prompt}
                    </Button>
                  ))}
                </Box>
              </Box>
            )}
            
            {/* Dynamic suggestion chips that appear after bot messages */}
            {messages.length > 0 && !loading && (
              <Box 
                sx={{ 
                  display: 'flex', 
                  flexWrap: 'wrap', 
                  gap: 1, 
                  mt: 2, 
                  justifyContent: 'center',
                  maxWidth: '700px',
                  mx: 'auto'
                }}
              >
                {suggestionPrompts.map((prompt, index) => (
                  <Chip
                    key={index}
                    label={prompt}
                    onClick={() => setInput(prompt)}
                    sx={{
                      bgcolor: '#121212',
                      color: '#d4af37',
                      border: '1px solid #d4af37',
                      fontSize: '0.85rem',
                      py: 0.5,
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: '#d4af37',
                        color: '#0a2463',
                      }
                    }}
                  />
                ))}
              </Box>
            )}
            {messages.map((msg, index) => (
              <Box
                key={index}
                display="flex"
                justifyContent={msg.type === 'user' ? 'flex-end' : 'flex-start'}
                mb={1}
              >
                <ChatMessage 
                  type={msg.type} 
                  answer={msg.content} 
                  references={msg.references || []}
                  cases={msg.cases || []}
                  stage={msg.stage || "initial"}
                />
              </Box>
            ))}
            {loading && (
              <Typography variant="body2" color="#d4af37" sx={{ mt: 1 }}>
                Assistant is typing...
              </Typography>
            )}
            <div ref={messagesEndRef} />
          </Box>
          <Box
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              borderTop: 1,
              borderColor: 'divider',
              mt: 2,
              bgcolor: '#1E293B',
              borderRadius: 2,
              boxShadow: 1,
              maxWidth: '900px',
              width: '100%',
              mx: 'auto',
            }}
          >
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                variant="outlined"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                disabled={loading}
                placeholder="Ask your legal question..."
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '10px',
                    color: '#d4af37',
                    '& fieldset': {
                      borderColor: '#d4af37',
                    },
                    '&:hover fieldset': {
                      borderColor: '#c4a030',
                    },
                  },
                  input: { color: '#fff' },
                }}
              />
              <Button
                variant="contained"
                onClick={handleSend}
                disabled={loading || !input.trim()}
                sx={{
                  bgcolor: '#d4af37',
                  color: '#0a2463',
                  fontWeight: 700,
                  fontSize: '1.1rem',
                  borderRadius: '10px',
                  px: 4,
                  '&:hover': {
                    bgcolor: '#c4a030',
                  },
                }}
              >
                {loading ? 'Sending...' : 'Send'}
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}