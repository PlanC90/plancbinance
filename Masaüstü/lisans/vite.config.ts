import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [
      react(),
      {
        name: 'api-endpoints',
        configureServer(server) {
          server.middlewares.use(async (req, res, next) => {
            // Admin Auth API
            if (req.url === '/api/admin-auth' && req.method === 'POST') {
              let body = '';
              req.on('data', chunk => {
                body += chunk.toString();
              });
              req.on('end', async () => {
                try {
                  const { password } = JSON.parse(body);

                  if (!password) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Password is required' }));
                    return;
                  }

                  const ADMIN_PASSWORD = env.ADMIN_PASSWORD || 'Ceyhun8387@';

                  if (password === ADMIN_PASSWORD) {
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: true, message: 'Authentication successful' }));
                  } else {
                    // Brute force koruması için delay
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    res.writeHead(401, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Invalid password' }));
                  }
                } catch (error) {
                  console.error('Auth error:', error);
                  res.writeHead(500, { 'Content-Type': 'application/json' });
                  res.end(JSON.stringify({ error: 'Internal server error' }));
                }
              });
            } else if (req.url === '/api/send-email' && req.method === 'POST') {
              let body = '';
              req.on('data', chunk => {
                body += chunk.toString();
              });
              req.on('end', async () => {
                try {
                  const Mailjet = (await import('node-mailjet')).default;
                  const data = JSON.parse(body);
                  
                  console.log('Sending email to:', data.email);
                  console.log('Using Mailjet API');
                  
                  const mailjet = Mailjet.apiConnect(
                    env.MAILJET_API_KEY || '',
                    env.MAILJET_SECRET_KEY || ''
                  );

                  await mailjet
                    .post('send', { version: 'v3.1' })
                    .request({
                      Messages: [
                        {
                          From: {
                            Email: env.EMAIL_FROM || 'license@planc.space',
                            Name: 'PlanC Trade Bot',
                          },
                          To: [
                            {
                              Email: data.email,
                            },
                          ],
                          Subject: 'Your PlanC Trade Bot License Key',
                          HTMLPart: `
                    <!DOCTYPE html>
                    <html>
                    <head>
                      <style>
                        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }
                        .container { max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
                        .header { background: rgba(255,255,255,0.05); padding: 40px 30px; text-align: center; border-bottom: 2px solid rgba(255,255,255,0.1); }
                        .header img { width: 80px; height: 80px; border-radius: 50%; margin-bottom: 20px; border: 3px solid rgba(255,255,255,0.2); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
                        .header h1 { color: #ffffff; margin: 0; font-size: 32px; text-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                        .content { background: #ffffff; padding: 40px 30px; }
                        .license-box { background: linear-gradient(135deg, #0f3460 0%, #16213e 100%); color: white; padding: 25px; border-radius: 12px; text-align: center; margin: 30px 0; box-shadow: 0 8px 16px rgba(0,0,0,0.3); border: 2px solid rgba(255,255,255,0.1); }
                        .license-key { font-size: 24px; font-weight: bold; letter-spacing: 2px; font-family: 'Courier New', monospace; word-break: break-all; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
                        .info { color: #555; line-height: 1.8; margin: 20px 0; }
                        .footer { background: rgba(0,0,0,0.2); padding: 30px; text-align: center; color: rgba(255,255,255,0.7); font-size: 14px; }
                        .button { display: inline-block; background: linear-gradient(135deg, #0f3460 0%, #16213e 100%); color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.4); border: 2px solid rgba(255,255,255,0.1); }
                        .highlight { background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; border-radius: 4px; margin: 20px 0; }
                      </style>
                    </head>
                    <body>
                      <div class="container">
                        <div class="header">
                          <img src="https://pbs.twimg.com/profile_images/1973360241547837441/zmewfn7J_400x400.jpg" alt="PlanC Logo" />
                          <h1>PlanC Trade Bot</h1>
                          <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Your License is Ready!</p>
                        </div>
                        <div class="content">
                          <p class="info">Congratulations! Your PlanC Trade Bot license has been approved and activated.</p>
                          
                          <div class="license-box">
                            <p style="margin: 0 0 10px 0; font-size: 14px; opacity: 0.9;">Your License Key</p>
                            <div class="license-key">${data.licenseKey}</div>
                          </div>

                          <div class="highlight">
                            <strong>⚠️ Important:</strong> Keep this license key secure. You'll need it to activate PlanC Trade Bot.
                          </div>

                          <p class="info"><strong>Next Steps:</strong></p>
                          <ol class="info">
                            <li>Download PlanC Trade Bot from our official website</li>
                            <li>Install and launch the application</li>
                            <li>Enter your license key when prompted</li>
                            <li>Start trading with professional automation!</li>
                          </ol>

                          <div style="text-align: center;">
                            <a href="https://planc.space" class="button">Visit PlanC.Space</a>
                          </div>

                          <p class="info" style="margin-top: 30px; font-size: 14px; color: #888;">
                            If you have any questions, feel free to contact our support team.
                          </p>
                        </div>
                        <div class="footer">
                          <p style="margin: 0 0 10px 0; color: rgba(255,255,255,0.9);"><strong>PlanC Trade Bot</strong></p>
                          <p style="margin: 0; font-size: 12px; color: rgba(255,255,255,0.6);">Powered by PLANC SPACE</p>
                        </div>
                      </div>
                    </body>
                    </html>
                          `,
                        },
                      ],
                    });

                  console.log('Email sent successfully via Mailjet!');
                  res.writeHead(200, { 'Content-Type': 'application/json' });
                  res.end(JSON.stringify({ success: true }));
                } catch (error) {
                  console.error('Email error:', error);
                  res.writeHead(500, { 'Content-Type': 'application/json' });
                  res.end(JSON.stringify({ error: 'Failed to send email', details: error instanceof Error ? error.message : String(error) }));
                }
              });
            } else {
              next();
            }
          });
        },
      },
    ],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  };
});
