import { useState } from 'react';
import { Send, CheckCircle, ExternalLink, Copy, Check } from 'lucide-react';
import { supabase } from '../lib/supabase';
import { translations, Language } from '../translations';

interface LicenseFormProps {
  language: Language;
}

const WALLET_ADDRESS = '0xbd63Ca73f0edD0E875434CcED1E7c9D970CF4e46';
const TOKEN_URL = 'https://omax.fun/token/0x022A26D6B758CB5f94671E880BBC22A69582690B';
const CHAINLIST_URL = 'https://chainlist.org/chain/311';

export function LicenseForm({ language }: LicenseFormProps) {
  const t = translations[language];
  const [formData, setFormData] = useState({
    email: '',
    wallet: '',
    paymentHash: '',
    confirmed: false,
  });
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  // Input Validation Functions (GÜVENLİK)
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateWalletAddress = (wallet: string): boolean => {
    // Ethereum address formatı: 0x + 40 hex karakter
    const walletRegex = /^0x[a-fA-F0-9]{40}$/;
    return walletRegex.test(wallet);
  };

  const validateHash = (hash: string): boolean => {
    // Transaction hash formatı: 0x + 64 hex karakter
    const hashRegex = /^0x[a-fA-F0-9]{64}$/;
    return hashRegex.test(hash);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Input Validation (GÜVENLİK)
    if (!validateEmail(formData.email)) {
      setError('Invalid email format');
      return;
    }

    if (!validateWalletAddress(formData.wallet)) {
      setError('Invalid wallet address format (must be 0x + 40 hex characters)');
      return;
    }

    if (!validateHash(formData.paymentHash)) {
      setError('Invalid payment hash format (must be 0x + 64 hex characters)');
      return;
    }

    if (!formData.confirmed) {
      setError('Please confirm that you have sent the payment');
      return;
    }

    setLoading(true);

    try {
      const { error: dbError } = await supabase
        .from('license_forms')
        .insert([
          {
            email: formData.email,
            wallet_address: formData.wallet,
            payment_hash: formData.paymentHash,
            language,
            status: 'pending',
          },
        ]);

      if (dbError) throw dbError;

      setSubmitted(true);
      setFormData({ email: '', wallet: '', paymentHash: '', confirmed: false });
    } catch (err) {
      setError('An error occurred. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const copyAddress = async () => {
    try {
      await navigator.clipboard.writeText(WALLET_ADDRESS);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const addOmaxNetwork = async () => {
    if (typeof window.ethereum !== 'undefined') {
      try {
        await window.ethereum.request({
          method: 'wallet_addEthereumChain',
          params: [
            {
              chainId: '0x137',
              chainName: 'Omax Network',
              rpcUrls: ['https://mainapi.omaxray.com'],
              nativeCurrency: {
                name: 'OMAX',
                symbol: 'OMAX',
                decimals: 18,
              },
              blockExplorerUrls: ['https://omaxray.com'],
            },
          ],
        });
      } catch (err) {
        console.error('Failed to add network:', err);
      }
    }
  };

  if (submitted) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12 px-6">
        <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-2xl p-8 backdrop-blur-sm">
          <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
          <h3 className="text-2xl font-bold text-white mb-3">{t.successTitle}</h3>
          <p className="text-gray-300">{t.successMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6">
      <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700 rounded-2xl p-8 shadow-2xl">
        <h2 className="text-3xl font-bold text-white mb-2">{t.licensingTitle}</h2>
        <p className="text-gray-400 mb-8">{t.licensingSubtitle}</p>

        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6 mb-8">
          <p className="text-sm text-gray-300 mb-3 font-semibold">{t.sendTo}</p>
          <div className="flex items-center gap-2 bg-gray-900/50 rounded-lg p-4 mb-4">
            <code className="text-blue-400 text-sm break-all flex-1">{WALLET_ADDRESS}</code>
            <button
              onClick={copyAddress}
              className="flex-shrink-0 p-2 hover:bg-gray-800 rounded-lg transition-all group relative"
              title="Copy address"
            >
              {copied ? (
                <Check className="w-5 h-5 text-green-400" />
              ) : (
                <Copy className="w-5 h-5 text-gray-400 group-hover:text-blue-400 transition-colors" />
              )}
            </button>
          </div>
          <p className="text-xs text-gray-400 mb-4">{t.network}</p>
          <div className="flex flex-col sm:flex-row gap-3">
            <a
              href={TOKEN_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-lg transition-all font-semibold text-sm"
            >
              <ExternalLink className="w-4 h-4" />
              {t.buyToken}
            </a>
            <button
              onClick={addOmaxNetwork}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white rounded-lg transition-all font-semibold text-sm"
            >
              <ExternalLink className="w-4 h-4" />
              {t.addNetwork}
            </button>
          </div>
          <a
            href={CHAINLIST_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white rounded-lg transition-all font-semibold text-sm mt-3"
          >
            <ExternalLink className="w-4 h-4" />
            ChainList
          </a>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-2">
              {t.formEmail}
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-2">
              {t.formWallet}
            </label>
            <input
              type="text"
              required
              value={formData.wallet}
              onChange={(e) => setFormData({ ...formData, wallet: e.target.value })}
              className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all font-mono text-sm"
              placeholder="0x..."
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-2">
              {t.formPayment}
            </label>
            <input
              type="text"
              required
              value={formData.paymentHash}
              onChange={(e) => setFormData({ ...formData, paymentHash: e.target.value })}
              className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all font-mono text-sm"
              placeholder="0x..."
            />
          </div>

          <label className="flex items-start gap-3 cursor-pointer group">
            <input
              type="checkbox"
              required
              checked={formData.confirmed}
              onChange={(e) => setFormData({ ...formData, confirmed: e.target.checked })}
              className="mt-1 w-5 h-5 rounded border-gray-600 bg-gray-900/50 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0"
            />
            <span className="text-sm text-gray-300 group-hover:text-white transition-colors">
              {t.formConfirm}
            </span>
          </label>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !formData.confirmed}
            className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-lg transition-all font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-blue-500/50"
          >
            <Send className="w-5 h-5" />
            {loading ? '...' : t.formSubmit}
          </button>
        </form>
      </div>
    </div>
  );
}
