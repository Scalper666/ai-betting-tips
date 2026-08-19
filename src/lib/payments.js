// Maps the payment-method labels used in countries.json to the guides that
// explain them, so a country page links its rails instead of listing dead text.
// Only methods with a guide appear here; everything else renders as plain text.
const MAP = {
  'M-Pesa': 'betting-with-mpesa',
  'M-Pesa (Vodacom)': 'betting-with-mpesa',
  'M-Pesa Ethiopia': 'betting-with-mpesa',
  'Airtel Money': 'betting-with-airtel-money',
  'MTN MoMo': 'betting-with-mtn-mobile-money',
  'MTN Mobile Money': 'betting-with-mtn-mobile-money',
  'Orange Money': 'betting-with-orange-money',
  telebirr: 'betting-with-telebirr',
  Paystack: 'betting-with-flutterwave-and-paystack',
  Flutterwave: 'betting-with-flutterwave-and-paystack',
  USSD: 'betting-with-flutterwave-and-paystack',
  PIX: 'betting-with-pix',
  PayPal: 'betting-with-paypal',
  Skrill: 'betting-with-skrill',
  iDEAL: 'betting-with-ideal',
  BLIK: 'betting-with-blik',
  Swish: 'betting-with-swish',
  'BankID + bank transfer': 'betting-with-swish',
  TWINT: 'betting-with-twint',
  UPI: 'betting-with-upi',
  'Visa/Mastercard': 'betting-with-debit-cards',
  Visa: 'betting-with-debit-cards',
  'Debit card': 'betting-with-debit-cards',
};

export const paymentGuide = (label) => MAP[label] ?? null;
