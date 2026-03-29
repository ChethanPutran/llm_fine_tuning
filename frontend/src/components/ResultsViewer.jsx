import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Box
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const ResultsViewer = ({ results, type }) => {
  if (!results) return null;
  
  const renderMetrics = () => {
    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Metric</TableCell>
              <TableCell align="right">Value</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(results.metrics || {}).map(([key, value]) => (
              <TableRow key={key}>
                <TableCell component="th" scope="row">
                  {key}
                </TableCell>
                <TableCell align="right">
                  {typeof value === 'number' ? value.toFixed(4) : value}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };
  
  const renderTrainingHistory = () => {
    if (!results.training_history) return null;
    
    return (
      <Box sx={{ height: 400, mt: 2 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={results.training_history}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="epoch" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="train_loss" stroke="#8884d8" />
            <Line type="monotone" dataKey="eval_loss" stroke="#82ca9d" />
            <Line type="monotone" dataKey="accuracy" stroke="#ffc658" />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    );
  };
  
  const renderDocuments = () => {
    if (!results.documents) return null;
    
    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Content Preview</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {results.documents.slice(0, 10).map((doc, idx) => (
              <TableRow key={idx}>
                <TableCell>{doc.id.substring(0, 8)}...</TableCell>
                <TableCell>
                  <Chip label={doc.source} size="small" />
                </TableCell>
                <TableCell>{doc.content.substring(0, 100)}...</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };
  
  const renderDeployment = () => {
    if (!results.endpoint) return null;
    
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Deployment Information
          </Typography>
          <Typography>
            <strong>Endpoint:</strong> {results.endpoint}
          </Typography>
          <Typography>
            <strong>Model ID:</strong> {results.model_id}
          </Typography>
          <Typography>
            <strong>Status:</strong> {results.status}
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle1">Sample API Call:</Typography>
            <Paper sx={{ p: 1, bgcolor: 'grey.100' }}>
              <code>
                curl -X POST {results.endpoint}/predict \
                  -H "Content-Type: application/json" \
                  -d '{{"text": "Your input text here"}}'
              </code>
            </Paper>
          </Box>
        </CardContent>
      </Card>
    );
  };
  
  switch (type) {
    case 'metrics':
      return renderMetrics();
    case 'training':
      return (
        <>
          {renderMetrics()}
          {renderTrainingHistory()}
        </>
      );
    case 'documents':
      return renderDocuments();
    case 'deployment':
      return renderDeployment();
    default:
      return null;
  }
};

export default ResultsViewer;