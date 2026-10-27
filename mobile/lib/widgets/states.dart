import 'package:flutter/material.dart';

import '../theme.dart';

class LoadingView extends StatelessWidget {
  const LoadingView(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const SizedBox(
          width: 28,
          height: 28,
          child: CircularProgressIndicator(strokeWidth: 3),
        ),
        const SizedBox(height: 12),
        Text(text, style: const TextStyle(color: Palette.muted)),
      ],
    ),
  );
}

class MessageView extends StatelessWidget {
  const MessageView({
    super.key,
    required this.title,
    required this.body,
    this.actionLabel,
    this.onAction,
    this.isError = false,
  });

  final String title;
  final String body;
  final String? actionLabel;
  final VoidCallback? onAction;
  final bool isError;

  @override
  Widget build(BuildContext context) => ListView(
    // A list so pull-to-refresh still works on an empty or failed screen.
    padding: const EdgeInsets.fromLTRB(24, 48, 24, 24),
    children: [
      Text(
        title,
        style: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: isError ? Palette.alarmCoralText : Palette.ink,
        ),
      ),
      const SizedBox(height: 8),
      Text(body, style: const TextStyle(color: Palette.ink, height: 1.4)),
      if (actionLabel != null) ...[
        const SizedBox(height: 16),
        Align(
          alignment: Alignment.centerLeft,
          child: OutlinedButton(onPressed: onAction, child: Text(actionLabel!)),
        ),
      ],
    ],
  );
}
