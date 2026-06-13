import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic> _data = {};
  bool _isLoading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    print('=== DASHBOARD INIT ===');
    _loadData();
  }

  Future<void> _loadData() async {
    print('=== LOAD DATA CALLED ===');
    setState(() {
      _isLoading = true;
      _error = '';
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('token');

      print('=== DASHBOARD LOAD ===');
      print('Token: $token');

      if (token == null) {
        print('No token, logging out');
        _logout();
        return;
      }

      print('Calling API...');
      final dashboard = await ApiService.getDashboard(token);
      print('Data received: $dashboard');

      setState(() {
        _data = dashboard;
        _isLoading = false;
      });
    } catch (e) {
      print('Error: $e');
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
    if (mounted) {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    print('=== BUILD DASHBOARD ===');
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        backgroundColor: Colors.green,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _logout,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error, size: 64, color: Colors.red),
                      const SizedBox(height: 16),
                      Text('Error: $_error'),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadData,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Card(
                        color: Colors.green.shade50,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            children: [
                              const Text(
                                'Today\'s Summary',
                                style: TextStyle(
                                    fontSize: 18, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 12),
                              Row(
                                children: [
                                  Expanded(
                                    child: Column(
                                      children: [
                                        const Icon(Icons.attach_money,
                                            size: 32, color: Colors.green),
                                        const SizedBox(height: 4),
                                        Text('Revenue',
                                            style: TextStyle(
                                                color: Colors.grey[600])),
                                        Text(
                                          '${(_data['today']?['revenue'] ?? 0).toStringAsFixed(0)} TZS',
                                          style: const TextStyle(
                                              fontSize: 16,
                                              fontWeight: FontWeight.bold),
                                        ),
                                      ],
                                    ),
                                  ),
                                  Expanded(
                                    child: Column(
                                      children: [
                                        const Icon(Icons.receipt,
                                            size: 32, color: Colors.blue),
                                        const SizedBox(height: 4),
                                        Text('Sales',
                                            style: TextStyle(
                                                color: Colors.grey[600])),
                                        Text(
                                          '${_data['today']?['sales_count'] ?? 0}',
                                          style: const TextStyle(
                                              fontSize: 16,
                                              fontWeight: FontWeight.bold),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            children: [
                              const Text(
                                'Overall Summary',
                                style: TextStyle(
                                    fontSize: 18, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 12),
                              _buildStatRow(
                                  'Total Products',
                                  '${_data['counts']?['total_products'] ?? 0}',
                                  Icons.inventory,
                                  Colors.orange),
                              _buildStatRow(
                                  'Total Customers',
                                  '${_data['counts']?['total_customers'] ?? 0}',
                                  Icons.people,
                                  Colors.purple),
                              _buildStatRow(
                                  'Low Stock',
                                  '${_data['counts']?['low_stock_products'] ?? 0}',
                                  Icons.warning,
                                  Colors.red),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }

  Widget _buildStatRow(String title, String value, IconData icon, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, size: 24, color: color),
          const SizedBox(width: 16),
          Expanded(child: Text(title, style: const TextStyle(fontSize: 14))),
          Text(value,
              style:
                  const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
