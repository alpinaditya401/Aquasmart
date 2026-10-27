import 'package:flutter/material.dart';

import 'api.dart';
import 'screens/alerts_screen.dart';
import 'screens/login_screen.dart';
import 'screens/ponds_screen.dart';
import 'theme.dart';

void main() => runApp(AquaSmartApp(api: ApiClient()));

class AquaSmartApp extends StatefulWidget {
  const AquaSmartApp({super.key, required this.api});

  final ApiClient api;

  @override
  State<AquaSmartApp> createState() => _AquaSmartAppState();
}

class _AquaSmartAppState extends State<AquaSmartApp> {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AquaSmart',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      home: widget.api.loggedIn
          ? HomeScreen(api: widget.api, onLoggedOut: () => setState(() {}))
          : LoginScreen(api: widget.api, onLoggedIn: () => setState(() {})),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.api, required this.onLoggedOut});

  final ApiClient api;
  final VoidCallback onLoggedOut;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tab = 0;
  int _unread = 0;
  final _ponds = GlobalKey<PondsScreenState>();
  final _alerts = GlobalKey<AlertsScreenState>();

  @override
  void initState() {
    super.initState();
    // Badge count before the alerts tab is ever opened.
    widget.api.alerts(limit: 1).then((r) {
      if (mounted) setState(() => _unread = r.$2);
    }, onError: (_) {});
  }

  Future<void> _logout() async {
    try {
      await widget.api.logout();
    } on ApiException {
      // The local session is cleared either way; the server cookie expires on its own.
    }
    widget.onLoggedOut();
  }

  void _sessionLost() {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Sesi berakhir. Silakan masuk lagi.')),
    );
    widget.onLoggedOut();
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.api.user;
    return Scaffold(
      appBar: AppBar(
        title: Text(_tab == 0 ? 'Kolam' : 'Peringatan'),
        actions: [
          IconButton(
            tooltip: 'Muat ulang',
            onPressed: () => _tab == 0
                ? _ponds.currentState?.refresh()
                : _alerts.currentState?.refresh(),
            icon: const Icon(Icons.refresh),
          ),
          PopupMenuButton<String>(
            tooltip: 'Akun',
            icon: const Icon(Icons.account_circle_outlined),
            onSelected: (v) => v == 'keluar' ? _logout() : null,
            itemBuilder: (_) => [
              PopupMenuItem(
                enabled: false,
                child: Text(
                  '${user?.name ?? ''} (${user?.role ?? ''})',
                  style: const TextStyle(color: Palette.ink),
                ),
              ),
              const PopupMenuItem(value: 'keluar', child: Text('Keluar')),
            ],
          ),
        ],
      ),
      body: IndexedStack(
        index: _tab,
        children: [
          PondsScreen(
            key: _ponds,
            api: widget.api,
            onSessionLost: _sessionLost,
          ),
          AlertsScreen(
            key: _alerts,
            api: widget.api,
            onCount: (n) => setState(() => _unread = n),
            onSessionLost: _sessionLost,
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.water_drop_outlined),
            selectedIcon: Icon(Icons.water_drop),
            label: 'Kolam',
          ),
          NavigationDestination(
            icon: Badge(
              isLabelVisible: _unread > 0,
              label: Text('$_unread'),
              child: const Icon(Icons.notifications_outlined),
            ),
            selectedIcon: Badge(
              isLabelVisible: _unread > 0,
              label: Text('$_unread'),
              child: const Icon(Icons.notifications),
            ),
            label: 'Peringatan',
          ),
        ],
      ),
    );
  }
}
