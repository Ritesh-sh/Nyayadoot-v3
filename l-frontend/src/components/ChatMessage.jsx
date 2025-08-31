import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Paper, Box, Typography, Collapse, Button, Divider, List, ListItem, ListItemText, Chip } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

export default function ChatMessage({ answer, type, references = [], cases = [], stage = "initial" }) {
  const isUser = type === 'user';
  const [showReferences, setShowReferences] = useState(false);
  const [showCases, setShowCases] = useState(false);
  
  const hasAdditionalInfo = !isUser && (references?.length > 0 || cases?.length > 0);
  
  // Format short answers to be more readable
  const formattedAnswer = answer?.length < 100 ? answer : answer;

  // Updated color palette for modern gold/blue style
  const colors = {
    user: {
      background: '#d4af37', // gold
      text: '#0a2463', // deep blue text
      border: '#c4a030',
    },
    bot: {
      background: '#1E293B', // deep blue
      text: '#F8FAFC', // light text
      border: '#232946',
    },
    codeBlock: {
      background: '#232946', // dark blue for code
      text: '#F8FAFC', // light text for code
      accent: '#d4af37', // gold accent for inline code
    }
  };

  const bubbleStyles = isUser
    ? {
        borderTopLeftRadius: 18,
        borderTopRightRadius: 0,
        borderBottomLeftRadius: 18,
        borderBottomRightRadius: 18,
        border: `2px solid ${colors.user.border}`,
        alignSelf: 'flex-end',
      }
    : {
        borderTopLeftRadius: 0,
        borderTopRightRadius: 18,
        borderBottomLeftRadius: 18,
        borderBottomRightRadius: 18,
        border: `2px solid ${colors.bot.border}`,
        alignSelf: 'flex-start',
      };

  return (
    <Paper
      elevation={4}
      sx={{
        p: 2.2,
        maxWidth: '75%',
        bgcolor: isUser ? colors.user.background : colors.bot.background,
        color: isUser ? colors.user.text : colors.bot.text,
        ...bubbleStyles,
        wordBreak: 'break-word',
        whiteSpace: 'pre-wrap',
        fontSize: '1.05rem',
        lineHeight: 1.7,
        fontWeight: 500,
        boxShadow: 4,
        transition: 'all 0.3s cubic-bezier(.4,2,.6,1)',
        mb: 0.5,
      }}
    >
      <ReactMarkdown
        components={{
          p: ({ node, ...props }) => <span {...props} />,
          a: ({ node, ...props }) => (
            <a 
              {...props} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{
                color: colors.codeBlock.accent,
                fontWeight: 600,
                textDecoration: 'underline',
                transition: 'all 0.2s ease',
                '&:hover': {
                  textDecoration: 'none',
                  opacity: 0.9
                }
              }}
            />
          ),
          code: ({ node, inline, className, ...props }) =>
            inline ? (
              <code
                style={{
                  backgroundColor: colors.codeBlock.accent,
                  color: colors.user.text,
                  padding: '2px 8px',
                  borderRadius: 4,
                  fontSize: '0.93em',
                  fontWeight: 600,
                }}
                {...props}
              />
            ) : (
              <pre
                style={{
                  backgroundColor: colors.codeBlock.background,
                  color: colors.codeBlock.text,
                  padding: '14px',
                  borderRadius: 8,
                  overflowX: 'auto',
                  fontSize: '0.97rem',
                  margin: 0,
                }}
              >
                <code {...props} />
              </pre>
            ),
          // Add special handling for links
          link: ({ node, ...props }) => (
            <a 
              {...props} 
              target="_blank" 
              rel="noopener noreferrer" 
              style={{
                color: '#d4af37',
                fontWeight: 'bold',
                textDecoration: 'underline'
              }}
            />
          )
        }}
      >
        {/* Process text to detect and convert URLs to links if not already formatted */}
        {formattedAnswer}
      </ReactMarkdown>

      {hasAdditionalInfo && (
        <Box sx={{ mt: 2, pt: 1, borderTop: `1px solid ${colors.bot.border}` }}>
          {references?.length > 0 && (
            <Box>
              <Button 
                variant="text" 
                size="small"
                onClick={() => setShowReferences(!showReferences)}
                endIcon={showReferences ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                sx={{ 
                  color: colors.codeBlock.accent,
                  textTransform: 'none',
                  fontWeight: 600,
                  py: 0.5
                }}
              >
                Legal References ({references.length})
              </Button>
              
              <Collapse in={showReferences}>
                <List dense sx={{ bgcolor: colors.codeBlock.background, borderRadius: 2, mt: 1 }}>
                  {references.map((ref, index) => (
                    <ListItem key={index} sx={{ py: 1 }}>
                      <ListItemText 
                        primary={
                          <Typography variant="body2" fontWeight="bold">
                            {ref.act} - Section {ref.section_number}
                          </Typography>
                        }
                        secondary={
                          <Typography variant="body2" sx={{ color: colors.bot.text, opacity: 0.9 }}>
                            {ref.summary}
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            </Box>
          )}
          
          {cases?.length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Button 
                variant="text" 
                size="small"
                onClick={() => setShowCases(!showCases)}
                endIcon={showCases ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                sx={{ 
                  color: colors.codeBlock.accent,
                  textTransform: 'none',
                  fontWeight: 600,
                  py: 0.5
                }}
              >
                Relevant Cases ({cases.length})
              </Button>
              
              <Collapse in={showCases}>
                <List dense sx={{ bgcolor: colors.codeBlock.background, borderRadius: 2, mt: 1 }}>
                  {cases.map((caseItem, index) => (
                    <ListItem key={index} sx={{ py: 1 }}>
                      <ListItemText 
                        primary={
                          <Typography variant="body2" fontWeight="bold">
                            {caseItem.title || caseItem.name || "Case " + (index + 1)}
                          </Typography>
                        }
                        secondary={
                          <>
                            {caseItem.citation && (
                              <Typography variant="body2" sx={{ color: colors.bot.text, opacity: 0.9 }}>
                                {caseItem.citation}
                              </Typography>
                            )}
                            {caseItem.summary && (
                              <Typography variant="body2" sx={{ color: colors.bot.text, opacity: 0.8, mt: 0.5 }}>
                                {caseItem.summary}
                              </Typography>
                            )}
                            {caseItem.url && (
                              <Button 
                                variant="outlined" 
                                size="small" 
                                href={caseItem.url} 
                                target="_blank"
                                sx={{ 
                                  mt: 1, 
                                  borderColor: colors.codeBlock.accent,
                                  color: colors.codeBlock.accent,
                                  '&:hover': {
                                    borderColor: colors.codeBlock.accent,
                                    bgcolor: 'rgba(212, 175, 55, 0.1)'
                                  }
                                }}
                              >
                                View Case
                              </Button>
                            )}
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            </Box>
          )}
        </Box>
      )}
    </Paper>
  );
}
