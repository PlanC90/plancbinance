import { useState, useEffect, useMemo } from 'react';
import { Shield, LogOut, Calendar, Mail, Wallet, Hash, CheckCircle2, Loader2, TrendingUp, Send, Coins, ExternalLink, CheckCircle, XCircle } from 'lucide-react';
import { supabase, LicenseForm } from '../lib/supabase';
import { translations, Language } from '../translations';

interface AdminPanelProps {
  language: Language;
}

// Server-side password verification via /api/admin-auth

export function AdminPanel({ language }: AdminPanelProps) {
  const t = translations[language];
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [forms, setForms] = useState<LicenseForm[]>([]);
  const [loading, setLoading] = useState(false);
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [verifyingHash, setVerifyingHash] = useState<string | null>(null);
  const [verificationResults, setVerificationResults] = useState<Record<string, { verified: boolean; amount?: string; from?: string; error?: string }>>({});
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 25;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      // Backend API ile şifre kontrolü (GÜVENLİ)
      const response = await fetch('/api/admin-auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setIsAuthenticated(true);
        loadForms();
      } else {
        setError('Invalid password');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadForms = async () => {
    setLoading(true);
    try {
      const { data, error: dbError } = await supabase
        .from('license_forms')
        .select('*')
        .order('created_at', { ascending: false });

      if (dbError) throw dbError;
      setForms(data || []);
    } catch (err) {
      console.error('Error loading forms:', err);
    } finally {
      setLoading(false);
    }
  };

  const verifyPayment = async (hash: string) => {
    setVerifyingHash(hash);
    try {
      console.log('🔍 Verifying payment hash:', hash);
      
      // Expected payment address
      const EXPECTED_ADDRESS = '0xbd63Ca73f0edD0E875434CcED1E7c9D970CF4e46';
      
      // Omax Network RPC endpoint
      const rpcUrl = 'https://mainapi.omaxray.com';
      
      const response = await fetch(rpcUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'eth_getTransactionByHash',
          params: [hash],
          id: 1
        })
      });
      
      const data = await response.json();
      console.log('📡 RPC Response:', data);
      
      if (data.result) {
        const tx = data.result;
        const toAddress = tx.to?.toLowerCase();
        const expectedAddress = EXPECTED_ADDRESS.toLowerCase();
        
        // Token kontrat adresi (PLANC Token)
        const TOKEN_CONTRACT = '0x022A26D6B758CB5f94671E880BBC22A69582690B'.toLowerCase();
        
        let isValid = false;
        let amount = '0';
        let transferType = '';
        
        // Case 1: Native OMAX Transfer
        if (toAddress === expectedAddress) {
          const amountInWei = parseInt(tx.value, 16);
          const amountInOmax = (amountInWei / 1e18).toFixed(4);
          amount = amountInOmax + ' OMAX';
          isValid = true;
          transferType = 'Native OMAX';
          console.log('✅ Native OMAX transfer verified!', { amount, from: tx.from, to: tx.to });
        }
        // Case 2: Token Transfer (ERC20)
        else if (toAddress === TOKEN_CONTRACT && tx.input && tx.input.length >= 138) {
          // ERC20 transfer function signature: 0xa9059cbb (transfer)
          const methodId = tx.input.substring(0, 10);
          
          if (methodId === '0xa9059cbb') {
            // Decode recipient address from input (32 bytes after method id)
            const recipientHex = '0x' + tx.input.substring(34, 74);
            const recipientAddress = recipientHex.toLowerCase();
            
            // Decode amount (next 32 bytes)
            const amountHex = '0x' + tx.input.substring(74, 138);
            const amountInWei = parseInt(amountHex, 16);
            const amountInTokens = (amountInWei / 1e18).toFixed(4);
            
            if (recipientAddress === expectedAddress) {
              amount = amountInTokens + ' PLANC';
              isValid = true;
              transferType = 'PLANC Token';
              console.log('✅ Token transfer verified!', { amount, from: tx.from, recipient: recipientAddress });
            } else {
              console.log('❌ Token sent to wrong address:', { expected: EXPECTED_ADDRESS, got: recipientAddress });
            }
          }
        }
        
        if (isValid) {
          setVerificationResults(prev => ({
            ...prev,
            [hash]: {
              verified: true,
              amount: `${amount} (${transferType})`,
              from: tx.from
            }
          }));
        } else {
          setVerificationResults(prev => ({
            ...prev,
            [hash]: {
              verified: false,
              error: toAddress === TOKEN_CONTRACT 
                ? 'Token farklı bir adrese gönderilmiş veya geçersiz transfer formatı!'
                : `Yanlış alıcı adresi! Ödeme farklı bir adrese gönderilmiş: ${tx.to}`
            }
          }));
          
          console.log('❌ Payment verification failed:', { expected: EXPECTED_ADDRESS, txTo: tx.to, input: tx.input?.substring(0, 50) });
        }
      } else {
        setVerificationResults(prev => ({
          ...prev,
          [hash]: {
            verified: false,
            error: 'Transaction bulunamadı! Hash geçersiz veya henüz blockchain\'e eklenmemiş.'
          }
        }));
        console.log('❌ Transaction not found');
      }
    } catch (err) {
      console.error('❌ Verification error:', err);
      setVerificationResults(prev => ({
        ...prev,
        [hash]: {
          verified: false,
          error: 'Doğrulama başarısız! Lütfen tekrar deneyin.'
        }
      }));
    } finally {
      setVerifyingHash(null);
    }
  };

  // İstatistikleri hesapla
  const stats = useMemo(() => {
    const totalSent = forms.filter(f => f.status === 'sent').length;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todaySent = forms.filter(f => {
      const formDate = new Date(f.created_at);
      formDate.setHours(0, 0, 0, 0);
      return f.status === 'sent' && formDate.getTime() === today.getTime();
    }).length;
    const totalTokens = totalSent * 100000000; // Her lisans 100,000,000 PLANC
    
    return { totalSent, todaySent, totalTokens };
  }, [forms]);

  // Sayfalama hesaplamaları
  const paginatedForms = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    return forms.slice(startIndex, endIndex);
  }, [forms, currentPage, ITEMS_PER_PAGE]);

  const totalPages = Math.ceil(forms.length / ITEMS_PER_PAGE);

  useEffect(() => {
    if (isAuthenticated) {
      loadForms();
      const interval = setInterval(loadForms, 10000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  // Form sayısı değiştiğinde ve mevcut sayfa geçerli değilse 1. sayfaya dön
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(1);
    }
  }, [forms.length, currentPage, totalPages]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 py-12">
        <div className="max-w-md w-full bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700 rounded-2xl p-8 shadow-2xl">
          <div className="flex items-center justify-center mb-6">
            <Shield className="w-12 h-12 text-blue-500" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-6 text-center">{t.adminLogin}</h2>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                {t.adminPassword}
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="••••••••"
                required
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-lg transition-all font-semibold"
            >
              {t.adminLogin}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-6 py-12">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-500" />
            <h1 className="text-3xl font-bold text-white">{t.adminTitle}</h1>
          </div>
          <button
            onClick={() => setIsAuthenticated(false)}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all"
          >
            <LogOut className="w-4 h-4" />
            {t.logout}
          </button>
        </div>

        {/* İstatistik Kartları */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Toplam Gönderilen Lisanslar */}
          <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/20 backdrop-blur-sm border border-blue-500/30 rounded-xl p-6 hover:scale-105 transition-transform">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-500/20 rounded-lg">
                <Send className="w-6 h-6 text-blue-400" />
              </div>
              <TrendingUp className="w-5 h-5 text-blue-400" />
            </div>
            <h3 className="text-gray-400 text-sm font-medium mb-1">Toplam Gönderilen</h3>
            <p className="text-3xl font-bold text-white">{stats.totalSent}</p>
            <p className="text-xs text-gray-500 mt-2">Lisans</p>
          </div>

          {/* Bugün Gönderilen */}
          <div className="bg-gradient-to-br from-green-500/20 to-green-600/20 backdrop-blur-sm border border-green-500/30 rounded-xl p-6 hover:scale-105 transition-transform">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-500/20 rounded-lg">
                <Calendar className="w-6 h-6 text-green-400" />
              </div>
              <TrendingUp className="w-5 h-5 text-green-400" />
            </div>
            <h3 className="text-gray-400 text-sm font-medium mb-1">Bugün Gönderilen</h3>
            <p className="text-3xl font-bold text-white">{stats.todaySent}</p>
            <p className="text-xs text-gray-500 mt-2">Lisans</p>
          </div>

          {/* Toplam Kazanılan Token */}
          <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/20 backdrop-blur-sm border border-purple-500/30 rounded-xl p-6 hover:scale-105 transition-transform">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-500/20 rounded-lg">
                <Coins className="w-6 h-6 text-purple-400" />
              </div>
              <TrendingUp className="w-5 h-5 text-purple-400" />
            </div>
            <h3 className="text-gray-400 text-sm font-medium mb-1">Toplam Kazanılan</h3>
            <p className="text-3xl font-bold text-white">{stats.totalTokens.toLocaleString()}</p>
            <p className="text-xs text-gray-500 mt-2">PLANC Token</p>
          </div>
        </div>

        {loading && forms.length === 0 ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          </div>
        ) : (
          <>
            {/* Toplam ve Sayfa Bilgisi */}
            <div className="bg-gradient-to-br from-gray-800/30 to-gray-900/30 backdrop-blur-sm border border-gray-700 rounded-xl p-4 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">
                  Toplam <span className="text-white font-semibold">{forms.length}</span> lisans isteği
                </span>
                <span className="text-gray-400">
                  Sayfa <span className="text-white font-semibold">{currentPage}</span> / <span className="text-white font-semibold">{totalPages || 1}</span>
                </span>
              </div>
            </div>

            <div className="grid gap-4">
            {paginatedForms.map((form) => (
              <div
                key={form.id}
                className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 hover:border-gray-600 transition-all"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="flex items-start gap-3">
                    <Mail className="w-5 h-5 text-blue-400 mt-1 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs text-gray-400 mb-1">{t.adminEmail}</p>
                      <p className="text-sm text-white break-all">{form.email}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Wallet className="w-5 h-5 text-green-400 mt-1 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs text-gray-400 mb-1">{t.adminWallet}</p>
                      <p className="text-xs text-white font-mono break-all">{form.wallet_address}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Hash className="w-5 h-5 text-orange-400 mt-1 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <p className="text-xs text-gray-400">{t.adminHash}</p>
                        <button
                          onClick={() => verifyPayment(form.payment_hash)}
                          disabled={verifyingHash === form.payment_hash}
                          className="text-xs px-2 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded transition-all disabled:opacity-50 flex items-center gap-1"
                          title="Verify Payment"
                        >
                          {verifyingHash === form.payment_hash ? (
                            <>
                              <Loader2 className="w-3 h-3 animate-spin" />
                              Doğrulanıyor...
                            </>
                          ) : (
                            <>
                              <CheckCircle className="w-3 h-3" />
                              Doğrula
                            </>
                          )}
                        </button>
                      </div>
                      <a
                        href={`https://omaxscan.com/tx/${form.payment_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-400 hover:text-blue-300 font-mono break-all underline-offset-2 hover:underline inline-flex items-center gap-1 group"
                      >
                        <span className="break-all">{form.payment_hash}</span>
                        <ExternalLink className="w-3 h-3 flex-shrink-0 opacity-60 group-hover:opacity-100 transition-opacity" />
                      </a>
                      {verificationResults[form.payment_hash] && (
                        <div className={`mt-2 p-2 rounded-lg text-xs ${
                          verificationResults[form.payment_hash].verified 
                            ? 'bg-green-500/10 border border-green-500/30' 
                            : 'bg-red-500/10 border border-red-500/30'
                        }`}>
                          {verificationResults[form.payment_hash].verified ? (
                            <div className="flex items-start gap-2">
                              <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                              <div>
                                <p className="text-green-400 font-semibold">✅ Ödeme Doğrulandı</p>
                                <p className="text-gray-300 mt-1">Miktar: <span className="font-mono text-green-400">{verificationResults[form.payment_hash].amount}</span></p>
                                <p className="text-gray-300 text-[10px] mt-1 break-all">Gönderen: <span className="font-mono">{verificationResults[form.payment_hash].from}</span></p>
                              </div>
                            </div>
                          ) : (
                            <div className="flex items-start gap-2">
                              <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                              <div className="flex-1 min-w-0">
                                <p className="text-red-400 font-semibold">❌ Ödeme Geçersiz</p>
                                <p className="text-gray-400 text-[10px] mt-1 break-words">{verificationResults[form.payment_hash].error}</p>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-purple-400 mt-1 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs text-gray-400 mb-1">{t.adminDate}</p>
                      <p className="text-sm text-white">
                        {new Date(form.created_at).toLocaleString()}
                      </p>
                      <span
                        className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-semibold ${
                          form.status === 'sent'
                            ? 'bg-green-500/20 text-green-400'
                            : form.status === 'approved'
                            ? 'bg-blue-500/20 text-blue-400'
                            : form.status === 'rejected'
                            ? 'bg-red-500/20 text-red-400'
                            : 'bg-yellow-500/20 text-yellow-400'
                        }`}
                      >
                        {form.status === 'pending' ? t.statusPending :
                         form.status === 'sent' ? t.statusSent :
                         form.status === 'approved' ? t.statusApproved :
                         form.status === 'rejected' ? t.statusRejected :
                         form.status}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 flex items-center justify-end gap-3">
                  {/* İlk Gönderim veya Henüz Gönderilmemiş */}
                  <button
                    onClick={async () => {
                      console.log('🚀 APPROVE BUTTON CLICKED!');
                      setApprovingId(form.id);
                      try {
                        // Generate license key
                        const licenseKey = `PlanC.Space-${Math.random().toString(36).substring(2, 10).toUpperCase()}-${Math.random().toString(36).substring(2, 10).toUpperCase()}-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
                        console.log('📧 Sending email to:', form.email);
                        console.log('🔑 License Key:', licenseKey);
                        
                        // Send email first
                        const sendEmail = true; // Set to false to disable email sending
                        
                        if (sendEmail) {
                          console.log('📤 Calling /api/send-email...');
                          const emailResponse = await fetch('/api/send-email', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                              email: form.email, 
                              licenseKey 
                            })
                          });
                          
                          console.log('📬 Email API Response:', emailResponse.status);
                          
                          if (!emailResponse.ok) {
                            const errorData = await emailResponse.json().catch(() => ({}));
                            console.error('❌ Email error:', errorData);
                            throw new Error(`Email sending failed: ${errorData.details || errorData.error || 'Unknown error'}`);
                          }
                          
                          console.log('✅ Email sent successfully!');
                        } else {
                          // Test mode: Show license key in alert
                          console.log('License Key:', licenseKey);
                          alert(`✅ License created!\n\nEmail: ${form.email}\nLicense Key: ${licenseKey}\n\n(Email sending is disabled for testing)`);
                        }
                        
                        // Update in database with "sent" status
                        console.log('💾 Updating database...');
                        const { error: updateError } = await supabase
                          .from('license_forms')
                          .update({ 
                            license_key: licenseKey, 
                            status: 'sent' 
                          })
                          .eq('id', form.id);
                        
                        if (updateError) {
                          console.error('❌ Database error:', updateError);
                          throw updateError;
                        }
                        
                        console.log('✅ Database updated!');
                        await loadForms();
                        console.log('🔄 Forms reloaded!');
                      } catch (e) {
                        console.error('❌ Full error:', e);
                        alert('Error: ' + (e instanceof Error ? e.message : 'Failed to send license'));
                      } finally {
                        console.log('🏁 Process completed!');
                        setApprovingId(null);
                      }
                    }}
                    disabled={approvingId === form.id || form.status === 'sent'}
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white disabled:opacity-60 transition-all ${
                      form.status === 'sent' 
                        ? 'bg-green-500' 
                        : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                  >
                    {approvingId === form.id ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        {t.adminSending}
                      </>
                    ) : form.status === 'sent' ? (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        {t.adminSent}
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        {t.adminApprove}
                      </>
                    )}
                  </button>

                  {/* Tekrar Gönder Butonu (Sadece 'sent' statusündekiler için) */}
                  {form.status === 'sent' && form.license_key && (
                    <button
                      onClick={async () => {
                        console.log('🔄 RESEND BUTTON CLICKED!');
                        setApprovingId(form.id);
                        try {
                          console.log('📧 Resending email to:', form.email);
                          console.log('🔑 Using existing License Key:', form.license_key);
                          
                          // Resend email with existing license key
                          console.log('📤 Calling /api/send-email...');
                          const emailResponse = await fetch('/api/send-email', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                              email: form.email, 
                              licenseKey: form.license_key 
                            })
                          });
                          
                          console.log('📬 Email API Response:', emailResponse.status);
                          
                          if (!emailResponse.ok) {
                            const errorData = await emailResponse.json().catch(() => ({}));
                            console.error('❌ Email error:', errorData);
                            throw new Error(`Email sending failed: ${errorData.details || errorData.error || 'Unknown error'}`);
                          }
                          
                          console.log('✅ Email resent successfully!');
                          alert('✅ Lisans email tekrar gönderildi!');
                        } catch (e) {
                          console.error('❌ Resend error:', e);
                          alert('❌ Hata: ' + (e instanceof Error ? e.message : 'Email gönderilemedi'));
                        } finally {
                          console.log('🏁 Resend completed!');
                          setApprovingId(null);
                        }
                      }}
                      disabled={approvingId === form.id}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white bg-orange-600 hover:bg-orange-700 disabled:opacity-60 transition-all"
                      title="Lisansı tekrar gönder"
                    >
                      {approvingId === form.id ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Gönderiliyor...
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          Tekrar Gönder
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            ))}

            {paginatedForms.length === 0 && !loading && (
              <div className="text-center py-12">
                <p className="text-gray-400">No license requests yet</p>
              </div>
            )}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700 rounded-lg text-white disabled:opacity-30 disabled:cursor-not-allowed hover:border-blue-500 transition-all"
              >
                « Önceki
              </button>
              
              <div className="flex items-center gap-2">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => {
                  // Akıllı sayfa gösterimi: ilk 3, son 3, ve mevcut sayfa civarı
                  const showPage = 
                    page === 1 || 
                    page === totalPages || 
                    (page >= currentPage - 1 && page <= currentPage + 1);
                  
                  const showEllipsis = 
                    (page === 2 && currentPage > 4) || 
                    (page === totalPages - 1 && currentPage < totalPages - 3);

                  if (showEllipsis) {
                    return <span key={page} className="text-gray-500 px-2">...</span>;
                  }
                  
                  if (!showPage) return null;

                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`min-w-[40px] h-[40px] rounded-lg transition-all ${
                        currentPage === page
                          ? 'bg-blue-600 text-white font-semibold scale-110 shadow-lg shadow-blue-500/50'
                          : 'bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700 text-gray-300 hover:border-blue-500 hover:text-white'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700 rounded-lg text-white disabled:opacity-30 disabled:cursor-not-allowed hover:border-blue-500 transition-all"
              >
                Sonraki »
              </button>
            </div>
          )}
          </>
        )}
      </div>
    </div>
  );
}
