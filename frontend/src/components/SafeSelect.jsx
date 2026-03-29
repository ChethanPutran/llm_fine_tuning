import React, { useId } from 'react';
import { FormControl, InputLabel, NativeSelect } from '@mui/material';

const SafeSelect = ({ label, value, onChange, disabled, options, sx, ...props }) => {
  const labelId = useId();

  return (
    <FormControl fullWidth sx={{ mb: 2, ...sx }} {...props}>
      <InputLabel id={labelId}>{label}</InputLabel>
      <NativeSelect
        aria-labelledby={labelId}
        value={value ?? ''}
        onChange={onChange}
        disabled={disabled}
        inputProps={{
          id: `${labelId}-input`,
        }}
      >
        {options?.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </NativeSelect>
    </FormControl>
  );
};

export default SafeSelect;
