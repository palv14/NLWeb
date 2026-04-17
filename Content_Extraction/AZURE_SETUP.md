# 🚀 Azure Speech Services Setup Guide

## Overview

Azure Speech Services is the **primary transcription method** for the SCORM content extractor. It provides superior video transcription capabilities:

- **Larger video files** (up to 500MB)
- **Longer videos** (up to 4 hours)
- **Better accuracy** and reliability
- **No rate limiting** issues
- **Enterprise-grade** performance

## 🔧 Setup Steps

### 1. Create Azure Speech Services Resource

1. **Go to Azure Portal**: https://portal.azure.com
2. **Create Resource**: Search for "Speech Services"
3. **Configure**:
   - **Subscription**: Choose your subscription
   - **Resource Group**: Create new or use existing
   - **Region**: Choose closest region (e.g., `eastus`, `westus2`)
   - **Name**: Give it a name (e.g., `my-speech-service`)
   - **Pricing Tier**: Start with `Free (F0)` for testing
4. **Create** the resource

### 2. Get Credentials

1. **Go to your Speech Service resource**
2. **Keys and Endpoint** section
3. **Copy**:
   - **Key 1** or **Key 2** (subscription key)
   - **Region** (e.g., `eastus`)

### 3. Set Environment Variables

```bash
# Set your Azure Speech Services credentials
export AZURE_SPEECH_KEY="your_subscription_key_here"
export AZURE_SPEECH_REGION="eastus"
```

**For Windows:**
```cmd
set AZURE_SPEECH_KEY=your_subscription_key_here
set AZURE_SPEECH_REGION=eastus
```

### 4. Install Azure Speech SDK

```bash
pip install azure-cognitiveservices-speech>=1.31.0
```

## 🧪 Testing Azure Integration

### Test Azure Speech Services

```bash
# Test Azure transcription on a large video
python3 Content_Extraction/azure_speech_integration.py
```

### Test Enhanced Extractor

```bash
# Run the extractor with Azure transcription
python3 Content_Extraction/test_comprehensive_extraction.py
```

## 📊 Why Azure Speech Services?

| Feature | Azure Speech Services | Other Services |
|---------|----------------------|----------------|
| **File Size Limit** | 500MB | ~10MB |
| **Duration Limit** | 4 hours | ~60 seconds |
| **Accuracy** | Excellent | Good |
| **Rate Limiting** | No | Yes |
| **Reliability** | High | Variable |
| **Cost** | Pay-per-use | Free (limited) |

## 💰 Pricing (Azure Speech Services)

- **Free Tier (F0)**: 5 hours/month free
- **Standard Tier (S0)**: $1.00 per hour
- **Custom Speech**: Additional costs for custom models

## 🎯 Expected Results

With Azure Speech Services, you should see:
- ✅ **All videos transcribed** (including large ones)
- ✅ **Better transcript quality**
- ✅ **No "Bad Request" errors**
- ✅ **No "Broken pipe" errors**
- ✅ **Consistent results**
- ✅ **Handles 182MB videos** that failed before

## 🔍 Troubleshooting

### Common Issues

1. **"Azure Speech SDK not available"**
   ```bash
   pip install azure-cognitiveservices-speech
   ```

2. **"Credentials not found"**
   ```bash
   export AZURE_SPEECH_KEY="your_key"
   export AZURE_SPEECH_REGION="your_region"
   ```

3. **"Authentication failed"**
   - Check your subscription key
   - Verify the region matches your resource

4. **"Quota exceeded"**
   - Upgrade to Standard tier
   - Check usage in Azure portal

### Logs

The extractor will show:
- `"Azure transcription successful for {video}"`
- `"Azure transcription failed for {video}"`

## 🚀 Production Deployment

For production use:

1. **Use Standard Tier** for unlimited usage
2. **Set up monitoring** in Azure portal
3. **Configure alerts** for quota limits
4. **Use Azure Key Vault** for secure credential storage
5. **Consider Custom Speech** for domain-specific terminology

## 📝 Example Output

```json
{
  "id": "transcript_content_azure_123",
  "title": "Video Transcript: Large Video File",
  "content": "Complete transcript from Azure Speech Services...",
  "content_type": "transcript_content",
  "metadata": {
    "source": "video_transcript",
    "extraction_method": "azure_speech_services",
    "service": "azure_speech",
    "duration": 180.5
  }
}
```

## 🎉 Success!

Once configured, Azure Speech Services will handle:
- **All video files** regardless of size
- **Better transcription quality**
- **Reliable processing**
- **No rate limiting issues**

Your SCORM content extractor now has enterprise-grade video transcription capabilities! 