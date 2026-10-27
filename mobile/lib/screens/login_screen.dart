import 'package:flutter/material.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets/logo_mark.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.api, required this.onLoggedIn});

  final ApiClient api;
  final VoidCallback onLoggedIn;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _kontak = TextEditingController();
  final _sandi = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _kontak.dispose();
    _sandi.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.api.login(_kontak.text.trim(), _sandi.text);
      widget.onLoggedIn();
    } on ApiException catch (e) {
      setState(
        () => _error = e.status == 401
            ? 'Email/nomor HP atau kata sandi salah.'
            : e.message,
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _form,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        const LogoMark(),
                        const SizedBox(width: 10),
                        const Text(
                          'AquaSmart',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w700,
                            letterSpacing: -0.5,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 28),
                    Text(
                      'Masuk',
                      style: Theme.of(context).textTheme.headlineMedium
                          ?.copyWith(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Pantau kualitas air dan kirim perintah ke perangkat kolam Anda.',
                      style: TextStyle(color: Palette.muted),
                    ),
                    const SizedBox(height: 24),
                    TextFormField(
                      controller: _kontak,
                      keyboardType: TextInputType.emailAddress,
                      autofillHints: const [AutofillHints.username],
                      textInputAction: TextInputAction.next,
                      decoration: const InputDecoration(
                        labelText: 'Email atau nomor HP',
                      ),
                      validator: (v) => (v == null || v.trim().isEmpty)
                          ? 'Isi email atau nomor HP.'
                          : null,
                    ),
                    const SizedBox(height: 14),
                    TextFormField(
                      controller: _sandi,
                      obscureText: true,
                      autofillHints: const [AutofillHints.password],
                      onFieldSubmitted: (_) => _submit(),
                      decoration: const InputDecoration(
                        labelText: 'Kata sandi',
                      ),
                      validator: (v) =>
                          (v == null || v.isEmpty) ? 'Isi kata sandi.' : null,
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 14),
                      Text(
                        _error!,
                        key: const Key('login-error'),
                        style: const TextStyle(color: Palette.alarmCoralText),
                      ),
                    ],
                    const SizedBox(height: 20),
                    FilledButton(
                      onPressed: _busy ? null : _submit,
                      child: Text(_busy ? 'Memeriksa...' : 'Masuk'),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      'Server: ${widget.api.baseUrl}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Palette.muted,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Belum punya akun? Daftar lewat dashboard web AquaSmart.',
                      style: TextStyle(fontSize: 12, color: Palette.muted),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
