import 'package:aquasmart_mobile/api.dart';
import 'package:aquasmart_mobile/format.dart';
import 'package:flutter_test/flutter_test.dart';

Reading _r(String provenance, {bool simulation = false}) => Reading(
  time: '',
  ph: 7,
  temperature: 27,
  turbidity: 10,
  simulation: simulation,
  provenance: provenance,
);

void main() {
  test('label sumber membedakan data contoh, manual, dan data lama', () {
    expect(labelSumber(_r('seed')), 'Data contoh');
    expect(labelSumber(_r('manual')), 'Input manual');
    expect(labelSumber(_r('legacy_unverified')), 'Data lama, belum diverifikasi');
    expect(labelSumber(_r('device')), 'Perangkat, kalibrasi belum diverifikasi');
    expect(labelSumber(_r('', simulation: true)), 'SIMULASI');
  });

  test('label provenance alert memakai kata yang sama dengan bacaan', () {
    expect(labelProvenance('seed'), 'Data contoh');
    expect(labelProvenance('simulation'), 'SIMULASI');
  });
}
