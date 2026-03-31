export const usePipelineStatus = (jobId, statusFn, onComplete) => {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      const { data } = await statusFn(jobId);
      setStatus(data.status);
      setProgress(data.progress);

      if (data.status === 'completed') {
        clearInterval(interval);
        if (onComplete) onComplete(data.result);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  return { status, progress };
};