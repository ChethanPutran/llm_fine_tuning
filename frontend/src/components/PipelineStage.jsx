import React, { useState, useMemo, useCallback, useEffect } from "react";
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  LinearProgress,
  Alert,
  TextField,
  Slider,
  Switch,
  FormControlLabel,
  Chip,
} from "@mui/material";
import SafeSelect from './SafeSelect'; 
import { PlayArrow, Stop, Settings, Refresh } from "@mui/icons-material";

const PipelineStage = ({
  stage,
  config,
  onStart,
  onStop,
  status,
  progress,
  error,
  result,
}) => {
  // Initialize state with proper defaults - using useMemo to avoid recalculating
  const initialConfig = useMemo(() => {
    const initialConfig = {};
    if (stage.options) {
      stage.options.forEach((option) => {
        // Use provided config value, or option default, or empty string
        if (config && config[option.key] !== undefined) {
          initialConfig[option.key] = config[option.key];
        } else if (option.default !== undefined) {
          initialConfig[option.key] = option.default;
        } else if (option.type === "checkbox") {
          initialConfig[option.key] = false;
        } else if (option.type === "slider") {
          initialConfig[option.key] = option.default || 50;
        } else {
          initialConfig[option.key] = option.values ? option.values[0] : "";
        }
      });
    }
    return initialConfig;
  }, [stage.options, config]); // Only recalculate when stage.options or config changes

  const [stageConfig, setStageConfig] = useState(initialConfig);

  useEffect(() => {
    setStageConfig(initialConfig);
  }, [initialConfig]);

  const handleConfigChange = useCallback((key, value) => {
    setStageConfig((prev) => ({ ...prev, [key]: value }));
    console.log(`Config changed: ${key} = ${value}`);
    if (stage.onConfigChange) {
      stage.onConfigChange(key, value);
    }
  }, [stage]);

  const displayConfig = stageConfig;

  const handleStart = useCallback(() => {
    // Validate required fields
    const missingFields = [];
    stage.options.forEach((option) => {
      if (option.required && !displayConfig[option.key]) {
        missingFields.push(option.label);
      }
    });

    if (missingFields.length > 0) {
      alert(`Please fill in: ${missingFields.join(", ")}`);
      return;
    }

    onStart(displayConfig);
  }, [stage.options, displayConfig, onStart]);

  const handleStop = useCallback(() => {
    if (window.confirm("Are you sure you want to stop this process?")) {
      onStop();
    }
  }, [onStop]);

  const handleReset = useCallback(() => {
    setStageConfig(initialConfig);
  }, [initialConfig]);

  

  const renderInput = useCallback((option) => {
    switch (option.type) {
      case "select":
        return (
          <SafeSelect
            key={option.key}
            label={option.label}
            value={displayConfig[option.key] || ""}
            onChange={(e) => handleConfigChange(option.key, e.target.value)}
            disabled={status === "running"}
            options={option.values}
          />
        );

      case "text":
      case "textarea":
        return (
          <TextField
            fullWidth
            multiline={option.type === "textarea"}
            rows={option.rows || 3}
            label={option.label}
            value={displayConfig[option.key] || ""}
            onChange={(e) => handleConfigChange(option.key, e.target.value)}
            disabled={status === "running"}
            placeholder={
              option.placeholder || `Enter ${option.label.toLowerCase()}`
            }
            sx={{ mb: 2 }}
          />
        );

      case "number":
        return (
          <TextField
            fullWidth
            type="number"
            label={option.label}
            value={displayConfig[option.key] || option.default || 0}
            onChange={(e) =>
              handleConfigChange(option.key, parseInt(e.target.value))
            }
            disabled={status === "running"}
            inputProps={{
              min: option.min,
              max: option.max,
              step: option.step || 1,
            }}
            sx={{ mb: 2 }}
          />
        );

      case "slider":
        return (
          <Box sx={{ mb: 2 }}>
            <Typography gutterBottom>{option.label}</Typography>
            <Slider
              value={displayConfig[option.key] || option.default || 50}
              onChange={(e, val) => handleConfigChange(option.key, val)}
              min={option.min || 0}
              max={option.max || 100}
              step={option.step || 1}
              disabled={status === "running"}
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="textSecondary">
              Value: {displayConfig[option.key] || option.default || 50}
            </Typography>
          </Box>
        );

      case "checkbox":
        return (
          <FormControlLabel
            control={
              <Switch
                checked={displayConfig[option.key] || false}
                onChange={(e) =>
                  handleConfigChange(option.key, e.target.checked)
                }
                disabled={status === "running"}
              />
            }
            label={option.label}
            sx={{ mb: 2 }}
          />
        );

      case "file":
        return (
          <Button
            variant="outlined"
            component="label"
            sx={{ mb: 2 }}
            disabled={status === "running"}
          >
            {option.label}
            <input
              type="file"
              hidden
              accept={option.accept}
              onChange={(e) =>
                handleConfigChange(option.key, e.target.files[0])
              }
            />
          </Button>
        );

      default:
        return (
          <SafeSelect
            key={option.key}
            label={option.label}
            value={displayConfig[option.key] || ""}
            onChange={(e) => handleConfigChange(option.key, e.target.value)}
            disabled={status === "running"}
            options={option.values}
          />
        );
    }
  }, [displayConfig, handleConfigChange, status]);

  return (
    <Card sx={{ mb: 3, position: "relative" }}>
      <CardContent>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <Typography variant="h5" component="h2" sx={{ flex: 1 }}>
            {stage.name}
          </Typography>
          {status === "running" && (
            <Chip
              label="Running"
              color="primary"
              size="small"
              icon={<Settings className="spin" />}
            />
          )}
          {status === "completed" && (
            <Chip label="Completed" color="success" size="small" />
          )}
          {status === "failed" && (
            <Chip label="Failed" color="error" size="small" />
          )}
        </Box>

        <Box sx={{ mb: 2 }}>
          {stage.options.map((option) => (
            <div key={option.key}>{renderInput(option)}</div>
          ))}
        </Box>

        {status === "running" && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress variant="determinate" value={progress || 0} />
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Progress: {progress || 0}% complete
            </Typography>
            {stage.message && (
              <Typography variant="caption" color="textSecondary">
                {stage.message}
              </Typography>
            )}
          </Box>
        )}

        {status === "failed" && error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => {}}>
            <Typography variant="subtitle2">Error:</Typography>
            {error}
          </Alert>
        )}

        {status === "completed" && result && (
          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="subtitle2">Completed successfully!</Typography>
            {result.output_path && (
              <Typography variant="caption">
                Output: {result.output_path}
              </Typography>
            )}
          </Alert>
        )}

        <Box sx={{ display: "flex", gap: 1, mt: 2 }}>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={handleStart}
            disabled={status === "running" || status === "completed"}
          >
            Start
          </Button>
          <Button
            variant="outlined"
            startIcon={<Stop />}
            onClick={handleStop}
            disabled={status !== "running"}
          >
            Stop
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleReset}
            disabled={status === "running"}
          >
            Reset
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default PipelineStage;
