# OpenAI Model Selection Feature

## Overview
I've implemented a comprehensive model selection feature for your Exam Helper application that allows users to:

1. **Choose from available OpenAI models** via a dropdown menu
2. **Automatically detect working models** for their API key
3. **Store the selected model** in the config file to avoid repeated scanning
4. **See the current model** in the main interface

## New Features Added

### 1. Model Detection (`llm_module.py`)
- Added `get_working_models()` method that tests each model with the user's API key
- Added `set_model()` and `get_current_model()` methods for model management
- Added caching to avoid repeated API calls (`models_checked` flag)
- Updated all API calls to use the selected model instead of hardcoded `gpt-3.5-turbo`

### 2. Configuration Updates (`config.json`)
- Added `openai_model` field to store the selected model (default: "gpt-3.5-turbo")
- Added `working_models` array to cache detected models

### 3. Settings Dialog Enhancement (`exam_helper.py`)
- Added model selection dropdown in the settings window
- Added "🔍 Scan Models" button to detect available models
- Added status indicator showing scan results
- Added helpful tip for new users
- Increased window size to accommodate new controls

### 4. Main Interface Updates
- Added model indicator (🤖 model-name) in the status bar
- Real-time model updates when settings are saved
- Automatic LLM client updates when model or API key changes

### 5. Demo and Testing
- Created `test_model_selection.py` for testing the functionality
- Created `demo_model_selection.py` for a standalone demo interface

## How It Works

### For Users:
1. **First Time Setup:**
   - Enter your OpenAI API key in Settings
   - Click "🔍 Scan Models" to detect available models
   - Select your preferred model from the dropdown
   - Save settings

2. **Daily Usage:**
   - The selected model is automatically used for all requests
   - Model name is displayed in the status bar (🤖 gpt-4o)
   - No need to scan again unless you change API keys

3. **Model Switching:**
   - Open Settings → Select different model → Save
   - Changes apply immediately without restarting

### For Developers:
- Models are tested with a simple "Hi" message (5 tokens max)
- Failed models are logged but don't break the scanning process
- Working models are cached until API key changes
- All existing functionality remains unchanged

## Supported Models
The system tests these common OpenAI models:
- `gpt-4o` (latest)
- `gpt-4o-mini` (cost-effective)
- `gpt-4-turbo` (advanced)
- `gpt-4` (standard)
- `gpt-3.5-turbo` (default/fallback)

## Benefits

1. **Cost Optimization:** Users can choose cheaper models like `gpt-4o-mini` for basic questions
2. **Performance:** Advanced users can select `gpt-4o` for complex problems
3. **Reliability:** Automatic fallback if a model becomes unavailable
4. **User Experience:** Clear indication of which model is being used
5. **Efficiency:** No repeated model scanning - cached results

## Error Handling
- Invalid API keys are detected during scanning
- Unavailable models are gracefully skipped
- Clear error messages guide users to solutions
- Fallback to default model if selected model fails

## Usage Examples

### Quick Setup:
1. Settings → Enter API key → Scan Models → Select `gpt-4o-mini` → Save
2. Status bar shows: "🤖 gpt-4o-mini"
3. All questions now use the selected model

### Power User:
1. Use `gpt-3.5-turbo` for quick factual questions
2. Switch to `gpt-4o` for complex problem-solving
3. Use `gpt-4o-mini` for cost-effective general use

The feature is fully backward compatible - existing users will continue using `gpt-3.5-turbo` by default until they choose to scan and select a different model.