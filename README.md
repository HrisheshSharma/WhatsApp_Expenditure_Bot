# WhatsApp Cloud API Bot

This project integrates WhatsApp Cloud API with a Python-based bot using Flask and Webhooks.

## Getting Started

### Prerequisites
1. [Meta Developer Account](https://developers.facebook.com/)
2. [WhatsApp Business App](https://developers.facebook.com/docs/development/create-an-app/)
3. [Ngrok Account](https://ngrok.com/)
4. Python environment (e.g., virtualenv, conda)
5. [Groq API Key](https://console.groq.com/playground) (Sign up if you don't have an account)

### Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Fill in the required values:
     - `APP_ID`, `APP_SECRET`
     - `ACCESS_TOKEN` (Generate a long-lived token from Meta Business settings)
     - `VERIFY_TOKEN` (Custom string for webhook verification)
     - `GROQ_API_KEY` (Get it from [Groq Playground](https://console.groq.com/playground) under API Keys)

### Running the Bot
1. **Start the Flask app**
   ```bash
   python run.py
   ```
2. **Expose the app using Ngrok**
   ```bash
   ngrok http 8000 --domain your-domain.ngrok-free.app
   ```
3. **Configure Webhooks**
   - Go to Meta App Dashboard > WhatsApp > Configuration
   - Set callback URL: `https://your-domain.ngrok-free.app/webhook`
   - Use `VERIFY_TOKEN` from `.env`
   - Subscribe to `messages`
   - Send a test message to confirm the integration

### Sending Messages
1. Select a test number from the API setup
2. Send a message using `requests` or `curl`:
   ```bash
   curl -X POST "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages" \
   -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
   -H "Content-Type: application/json" \
   -d '{"messaging_product": "whatsapp", "to": "RECIPIENT_WAID", "type": "text", "text": {"body": "Hello World"}}'
   ```
3. Modify `generate_response()` in `whatsapp_utils.py` to customize replies.

### Deploying in Production
- **Use a permanent phone number** ([Guide](https://developers.facebook.com/docs/whatsapp/phone-numbers/))
- **Move from test to production API settings**
- **Ensure secure storage of access tokens**

## Additional Resources
- [WhatsApp Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Meta Webhooks Guide](https://developers.facebook.com/docs/graph-api/webhooks/getting-started)
- [Datalumina](https://www.datalumina.com/) (Original project inspiration)

### License
This project was originally inspired by work from [Datalumina](https://www.datalumina.com/) and has been heavily modified for specific use cases. Feel free to share and modify for your needs.

