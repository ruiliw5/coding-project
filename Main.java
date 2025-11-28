package labs.lab9;

import javax.swing.*;
import javax.swing.border.*;
import java.awt.*;
import java.awt.event.*;
import java.text.DecimalFormat;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class Main extends JFrame {
    // Model classes
    static class InvoiceItem {
        String description;
        double unitPrice;
        int quantity;
        
        public InvoiceItem(String description, double unitPrice, int quantity) {
            this.description = description;
            this.unitPrice = unitPrice;
            this.quantity = quantity;
        }
        
        public double getTotal() {
            return unitPrice * quantity;
        }
        
        @Override
        public String toString() {
            DecimalFormat df = new DecimalFormat("0.00");
            return description + " ($" + df.format(unitPrice) + " x " + quantity + " = $" + df.format(getTotal()) + ")";
        }
    }
    
    // UI Components
    private JTextArea billToTextArea, shipToTextArea;
    private JComboBox<String> stateComboBox;
    private JCheckBox premiumCustomerCheckBox;
    private JRadioButton noDiscountRadio, discount5Radio, discount10Radio, discount15Radio, discount20Radio;
    private ButtonGroup discountGroup;
    private JTextField invoiceNumberField;
    private JLabel invoiceNumberLabel, invoiceDateLabel, dueDateLabel;
    private JList<InvoiceItem> itemsList;
    private DefaultListModel<InvoiceItem> itemsListModel;
    private JLabel subtotalLabel, taxLabel, taxTextLabel, discountLabel, totalLabel;
    private JButton addItemButton;
    
    // Data
    private ArrayList<InvoiceItem> items = new ArrayList<>();
    private Map<String, Double> stateTaxRates = new HashMap<>();
    private int invoiceNumber = 1;
    private static final double PREMIUM_DISCOUNT = 10.0;
    
    public Main(String name, String id) {
        setTitle("Invoicer - " + name + " - " + id);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(700, 1000);
        setLayout(new BorderLayout(10, 10));
        
        // Initialize tax rates
        initTaxRates();
        
        // Create menu bar
        JMenuBar menuBar = new JMenuBar();
        JMenu fileMenu = new JMenu("File");
        JMenuItem exitMenuItem = new JMenuItem("Exit");
        exitMenuItem.addActionListener(e -> System.exit(0));
        fileMenu.add(exitMenuItem);
        
        JMenu invoiceMenu = new JMenu("Invoice");
        JMenuItem newInvoiceMenuItem = new JMenuItem("New Invoice");
        newInvoiceMenuItem.addActionListener(e -> createNewInvoice());
        invoiceMenu.add(newInvoiceMenuItem);
        
        menuBar.add(fileMenu);
        menuBar.add(invoiceMenu);
        setJMenuBar(menuBar);
        
        // Main panel
        JPanel mainPanel = new JPanel();
        mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
        mainPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
       
        
        // Customer info section
        JPanel customerPanel = new JPanel(new BorderLayout());
        customerPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createEtchedBorder(), "Customer Info"));
        
        // Bill To and Ship To panels in a single row
        JPanel addressPanel = new JPanel(new GridLayout(1, 2, 10, 0));
        addressPanel.setBorder(BorderFactory.createEmptyBorder(10, 5, 10, 5));
        
        JPanel billToPanel = new JPanel(new BorderLayout(0, 3)); // Add gap between label and text area
        billToPanel.add(new JLabel("Bill To:"), BorderLayout.NORTH);
        billToTextArea = new JTextArea(2, 6);  // 3 rows for better vertical presentation
        billToTextArea.setLineWrap(true);      // Enable line wrapping
        billToTextArea.setWrapStyleWord(true); // Wrap at word boundaries
        JScrollPane billToScrollPane = new JScrollPane(billToTextArea);
        billToScrollPane.setPreferredSize(new Dimension(100, 40));  // Slightly taller for better proportions
        billToPanel.add(billToScrollPane, BorderLayout.CENTER);

        // Ship To panel
        JPanel shipToPanel = new JPanel(new BorderLayout(0, 3)); // Add gap between label and text area
        shipToPanel.add(new JLabel("Ship To:"), BorderLayout.NORTH);
        shipToTextArea = new JTextArea(2, 6);  // 3 rows for better vertical presentation
        shipToTextArea.setLineWrap(true);      // Enable line wrapping
        shipToTextArea.setWrapStyleWord(true); // Wrap at word boundaries
        JScrollPane shipToScrollPane = new JScrollPane(shipToTextArea);
        shipToScrollPane.setPreferredSize(new Dimension(100, 40));  // Slightly taller for better proportions
        shipToPanel.add(shipToScrollPane, BorderLayout.CENTER);
        
        customerPanel.setBorder(BorderFactory.createCompoundBorder(
        	    BorderFactory.createTitledBorder(BorderFactory.createEtchedBorder(), "Customer Info"),
        	    BorderFactory.createEmptyBorder(5, 10, 10, 10)));

        addressPanel.add(billToPanel);
        addressPanel.add(shipToPanel);
        customerPanel.add(addressPanel, BorderLayout.CENTER);
        
        // State, Premium Customer, and Discount
        JPanel customerDetailsPanel = new JPanel(new GridLayout(3, 1));

        // State selection row
        JPanel stateRow = new JPanel(new FlowLayout(FlowLayout.LEFT));
        stateRow.add(new JLabel("State:"));
        String[] states = {"AK", "CA", "HI", "ID", "IL", "IN", "LA", "MI", "NY", "WI"};
        stateComboBox = new JComboBox<>(states);
        stateComboBox.addActionListener(e -> recalculateTotals());
        stateRow.add(stateComboBox);
        customerDetailsPanel.add(stateRow);

        // Premium customer row
        JPanel premiumRow = new JPanel(new FlowLayout(FlowLayout.LEFT));
        premiumCustomerCheckBox = new JCheckBox("Premium Customer?");
        premiumCustomerCheckBox.setSelected(false);
        premiumCustomerCheckBox.addActionListener(e -> recalculateTotals());
        premiumRow.add(premiumCustomerCheckBox);
        customerDetailsPanel.add(premiumRow);

        // Create radio buttons
        noDiscountRadio = new JRadioButton("None");
        discount5Radio = new JRadioButton("5%");
        discount10Radio = new JRadioButton("10%");
        discount15Radio = new JRadioButton("15%");
        discount20Radio = new JRadioButton("20%");
        noDiscountRadio.setSelected(true);

        // Group the radio buttons
        discountGroup = new ButtonGroup();
        discountGroup.add(noDiscountRadio);
        discountGroup.add(discount5Radio);
        discountGroup.add(discount10Radio);
        discountGroup.add(discount15Radio);
        discountGroup.add(discount20Radio);

        // Add action listeners for recalculation
        ActionListener discountListener = e -> recalculateTotals();
        noDiscountRadio.addActionListener(discountListener);
        discount5Radio.addActionListener(discountListener);
        discount10Radio.addActionListener(discountListener);
        discount15Radio.addActionListener(discountListener);
        discount20Radio.addActionListener(discountListener);

        // Discount/coupon row
        JPanel discountRow = new JPanel(new FlowLayout(FlowLayout.LEFT));
        discountRow.add(new JLabel("Coupon:"));
        discountRow.add(noDiscountRadio);
        discountRow.add(discount5Radio);
        discountRow.add(discount10Radio);
        discountRow.add(discount15Radio);
        discountRow.add(discount20Radio);
        customerDetailsPanel.add(discountRow);

        customerPanel.add(customerDetailsPanel, BorderLayout.SOUTH);
        
        // Invoice Info section
        JPanel invoiceInfoPanel = new JPanel(new BorderLayout());
        invoiceInfoPanel.setBorder(BorderFactory.createTitledBorder(
                BorderFactory.createEtchedBorder(), "Invoice Info"));

        // Create a panel with a vertical BoxLayout instead of GridLayout to avoid extra spacing
        JPanel invoiceFieldsPanel = new JPanel();
        invoiceFieldsPanel.setLayout(new BoxLayout(invoiceFieldsPanel, BoxLayout.Y_AXIS));

        // Invoice Number
        JPanel numPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        numPanel.add(new JLabel("Invoice Number:"));
        // Use the class member variable instead of creating a new local variable
        invoiceNumberLabel = new JLabel(String.valueOf(invoiceNumber));
        numPanel.add(invoiceNumberLabel);
        invoiceFieldsPanel.add(numPanel);

        // Invoice Date
        JPanel datePanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        datePanel.add(new JLabel("Invoice Date:"));
        LocalDate today = LocalDate.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        // Use the class member variable instead of creating a new local variable
        invoiceDateLabel = new JLabel(today.format(formatter));
        datePanel.add(invoiceDateLabel);
        invoiceFieldsPanel.add(datePanel);

        // Due Date
        JPanel duePanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        duePanel.add(new JLabel("Due Date:"));
        LocalDate dueDate = today.plusDays(30);
        // Use the class member variable instead of creating a new local variable
        dueDateLabel = new JLabel(dueDate.format(formatter));
        duePanel.add(dueDateLabel);
        invoiceFieldsPanel.add(duePanel);

        // Add the fields panel to the invoice info panel
        invoiceInfoPanel.add(invoiceFieldsPanel, BorderLayout.NORTH);
        
        // Items section
        JPanel itemsPanel = new JPanel(new BorderLayout());
        itemsPanel.setBorder(BorderFactory.createTitledBorder("Items"));
        
        itemsListModel = new DefaultListModel<>();
        itemsList = new JList<>(itemsListModel);
        JScrollPane itemsScrollPane = new JScrollPane(itemsList);
        itemsScrollPane.setPreferredSize(new Dimension(600, 100));
        itemsPanel.add(itemsScrollPane, BorderLayout.CENTER);
        
        // Create a panel to hold items and button separately
        JPanel itemsContainerPanel = new JPanel(new BorderLayout());
        itemsContainerPanel.add(itemsPanel, BorderLayout.CENTER);
        
        // Add Item button
        addItemButton = new JButton("Add Item");
        addItemButton.addActionListener(e -> showAddItemDialog());
        
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.CENTER));
        buttonPanel.add(addItemButton);
        itemsContainerPanel.add(buttonPanel, BorderLayout.SOUTH);
        
        // Create a panel to hold both the items container panel and totals panel
        JPanel itemsAndTotalsPanel = new JPanel(new BorderLayout());
        itemsAndTotalsPanel.add(itemsPanel, BorderLayout.CENTER);
        
        // Total calculation panel
        JPanel totalsPanel = new JPanel(new BorderLayout());
        
        // Add Item button on the center side of totals panel
        addItemButton = new JButton("Add Item");
        addItemButton.addActionListener(e -> showAddItemDialog());
        
        JPanel addButtonPanel = new JPanel(new FlowLayout(FlowLayout.CENTER));
        addButtonPanel.add(addItemButton);
        totalsPanel.add(addButtonPanel, BorderLayout.CENTER);
        
        // Create panel for totals with BoxLayout for better control
        JPanel totalsGridPanel = new JPanel();
        totalsGridPanel.setLayout(new BoxLayout(totalsGridPanel, BoxLayout.Y_AXIS));
        totalsGridPanel.setBorder(BorderFactory.createEmptyBorder(10, 0, 10, 0));

        // Create each row as a separate panel with FlowLayout.RIGHT
        JPanel subtotalRow = new JPanel(new FlowLayout(FlowLayout.RIGHT, 15, 0)); 
        JLabel subtotalTextLabel = new JLabel("Subtotal:");
        subtotalLabel = new JLabel("$0.00");
        subtotalRow.add(subtotalTextLabel);
        subtotalRow.add(subtotalLabel);

        JPanel taxRow = new JPanel(new FlowLayout(FlowLayout.RIGHT, 15, 0));
        taxTextLabel = new JLabel("Sales Tax (0.00%):");       
        taxLabel = new JLabel("$0.00");
        taxRow.add(taxTextLabel);
        taxRow.add(taxLabel);

        JPanel discountRow2 = new JPanel(new FlowLayout(FlowLayout.RIGHT, 15, 0));
        JLabel discountTextLabel = new JLabel("Discount:");
        discountLabel = new JLabel("$0.00");
        discountRow2.add(discountTextLabel);
        discountRow2.add(discountLabel);

        JPanel totalRow = new JPanel(new FlowLayout(FlowLayout.RIGHT, 15, 0));
        JLabel totalTextLabel = new JLabel("TOTAL:");
        totalTextLabel.setFont(totalTextLabel.getFont().deriveFont(Font.BOLD));
        totalLabel = new JLabel("$0.00");
        totalLabel.setFont(totalLabel.getFont().deriveFont(Font.BOLD));
        totalRow.add(totalTextLabel);
        totalRow.add(totalLabel);

        // Add some vertical spacing between rows 
        totalsGridPanel.add(subtotalRow);
        totalsGridPanel.add(Box.createVerticalStrut(10));
        totalsGridPanel.add(taxRow);
        totalsGridPanel.add(Box.createVerticalStrut(10));
        totalsGridPanel.add(discountRow2);
        totalsGridPanel.add(Box.createVerticalStrut(10));
        totalsGridPanel.add(totalRow);

        totalsPanel.add(totalsGridPanel, BorderLayout.EAST);
        
        // Add the combined panel to the items and totals panel
        itemsAndTotalsPanel.add(totalsPanel, BorderLayout.SOUTH);
        
        // Add the combined panel to the invoice info panel
        invoiceInfoPanel.add(itemsAndTotalsPanel, BorderLayout.CENTER);
        
        // Add all panels to the main panel
        mainPanel.add(customerPanel);
        mainPanel.add(Box.createVerticalStrut(10));
        mainPanel.add(invoiceInfoPanel);
        
        add(mainPanel, BorderLayout.CENTER);
        
        recalculateTotals();
    }
    
    private void initTaxRates() {
        stateTaxRates.put("AK", 1.82);
        stateTaxRates.put("CA", 8.85);
        stateTaxRates.put("HI", 4.50);
        stateTaxRates.put("ID", 6.03);
        stateTaxRates.put("IL", 8.85);
        stateTaxRates.put("IN", 7.00);
        stateTaxRates.put("LA", 9.56);
        stateTaxRates.put("MI", 6.00);
        stateTaxRates.put("NY", 8.53);
        stateTaxRates.put("WI", 5.70);
    }
    
    private void addItem(String description, double unitPrice, int quantity) {
        InvoiceItem item = new InvoiceItem(description, unitPrice, quantity);
        items.add(item);
    }
    
    private void showAddItemDialog() {
        // Variables to store the values between dialog reopenings
        String descValue = "";
        String priceValue = "";
        String qtyValue = "";
        
        while (true) {
            // Create panel for the dialog contents
            JPanel panel = new JPanel(new GridBagLayout());
            panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
            
            GridBagConstraints gbc = new GridBagConstraints();
            gbc.fill = GridBagConstraints.HORIZONTAL;
            gbc.insets = new Insets(5, 5, 5, 5);
            
            // Description field
            gbc.gridx = 0;
            gbc.gridy = 0;
            gbc.anchor = GridBagConstraints.EAST;
            panel.add(new JLabel("Description:"), gbc);
            
            gbc.gridx = 1;
            gbc.gridy = 0;
            gbc.anchor = GridBagConstraints.WEST;
            JTextField descField = new JTextField(20);
            descField.setText(descValue); // Set the stored value
            panel.add(descField, gbc);
            
            // Center panel for unit price
            JPanel pricePanel = new JPanel(new FlowLayout(FlowLayout.CENTER));
            JLabel priceLabel = new JLabel("Unit Price:");
            pricePanel.add(priceLabel);
            
            JTextField priceField = new JTextField(10); // Made longer (was 8)
            priceField.setText(priceValue); // Set the stored value
            pricePanel.add(priceField);
            
            gbc.gridx = 0;
            gbc.gridy = 1;
            gbc.gridwidth = 2; // Span both columns
            gbc.anchor = GridBagConstraints.CENTER;
            panel.add(pricePanel, gbc);
            
            // Center panel for quantity
            JPanel qtyPanel = new JPanel(new FlowLayout(FlowLayout.CENTER));
            JLabel qtyLabel = new JLabel("Quantity:");
            qtyPanel.add(qtyLabel);
            
            JTextField qtyField = new JTextField(10); // Made longer (was 8)
            qtyField.setText(qtyValue); // Set the stored value
            qtyPanel.add(qtyField);
            
            gbc.gridx = 0;
            gbc.gridy = 2;
            gbc.gridwidth = 2; // Span both columns
            panel.add(qtyPanel, gbc);
            
            // Show the dialog with OK and Cancel options
            int result = JOptionPane.showConfirmDialog(
                this, 
                panel, 
                "Add Item", 
                JOptionPane.OK_CANCEL_OPTION, 
                JOptionPane.PLAIN_MESSAGE
            );
            
            // If user clicked Cancel or closed the dialog
            if (result != JOptionPane.OK_OPTION) {
                break;
            }
            
            // Store the current values
            descValue = descField.getText().trim();
            priceValue = priceField.getText().trim();
            qtyValue = qtyField.getText().trim();
            
            // Validate input
            boolean valid = true;
            
            if (descValue.isEmpty()) {
                valid = false;
            }
            
            double unitPrice = 0;
            try {
                unitPrice = Double.parseDouble(priceValue);
                if (unitPrice <= 0) {
                    valid = false;
                }
            } catch (NumberFormatException ex) {
                valid = false;
            }
            
            int quantity = 0;
            try {
                quantity = Integer.parseInt(qtyValue);
                if (quantity <= 0) {
                    valid = false;
                }
            } catch (NumberFormatException ex) {
                valid = false;
            }
            
            if (valid) {
                addItem(descValue, unitPrice, quantity);
                refreshItemsList();
                recalculateTotals();
                break;
            }
            // If not valid, the while loop continues and reopens the dialog
            // with the stored values already in the fields
        }
    }
    
    private void refreshItemsList() {
        itemsListModel.clear();
        for (InvoiceItem item : items) {
            itemsListModel.addElement(item);
        }
    }
    
    private void recalculateTotals() {
        // Get the tax rate for the selected state
        String selectedState = (String) stateComboBox.getSelectedItem();
        double taxRate = stateTaxRates.getOrDefault(selectedState, 0.0);
        
        // Calculate subtotal
        double subtotal = 0;
        for (InvoiceItem item : items) {
            subtotal += item.getTotal();
        }
        
        // Calculate tax (based on subtotal)
        double tax = subtotal * (taxRate / 100);
        
        // Calculate coupon discount
        double discountRate = 0;
        if (discount5Radio.isSelected()) {
            discountRate = 5;
        } else if (discount10Radio.isSelected()) {
            discountRate = 10;
        } else if (discount15Radio.isSelected()) {
            discountRate = 15;
        } else if (discount20Radio.isSelected()) {
            discountRate = 20;
        }
        
        double couponDiscount = subtotal * (discountRate / 100);
        
        // Calculate premium customer discount
        double premiumDiscount = 0;
        if (premiumCustomerCheckBox.isSelected()) {
            premiumDiscount = PREMIUM_DISCOUNT;
        }
        
        // Total discount
        double totalDiscount = couponDiscount + premiumDiscount;
        
        // Calculate total
        double total = subtotal + tax - totalDiscount;
        
        // Format and update labels
        DecimalFormat currencyFormat = new DecimalFormat("$#,##0.00");
        DecimalFormat percentFormat = new DecimalFormat("0.00");
        
        // Update tax rate text with current percentage
        taxTextLabel.setText("Sales Tax (" + percentFormat.format(taxRate) + "%):");
        
        subtotalLabel.setText(currencyFormat.format(subtotal));
        taxLabel.setText(currencyFormat.format(tax));
        
        if (totalDiscount > 0) {
            discountLabel.setText("-" + currencyFormat.format(totalDiscount));
        } else {
            discountLabel.setText(currencyFormat.format(0));
        }
        
        totalLabel.setText(currencyFormat.format(total));
    }
    
    private void createNewInvoice() {
        // Clear items
        items.clear();
        refreshItemsList();
        
        // Increment invoice number
        invoiceNumber++;
        invoiceNumberLabel.setText(String.valueOf(invoiceNumber));
        
        // Update dates
        LocalDate today = LocalDate.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        invoiceDateLabel.setText(today.format(formatter));
        dueDateLabel.setText(today.plusDays(30).format(formatter));
        
        // Reset other fields to defaults
        billToTextArea.setText("");
        shipToTextArea.setText("");
        stateComboBox.setSelectedItem("CA");
        premiumCustomerCheckBox.setSelected(false);
        noDiscountRadio.setSelected(true);
        
        // Recalculate totals
        recalculateTotals();
    }
    
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
        	Main app = new Main("Ruilin Wu", "51084996");
            app.setVisible(true);
        });
    }
}